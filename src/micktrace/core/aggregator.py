"""In-memory log aggregation with smart buffering and analysis."""

import time
import threading
from typing import Dict, List, Optional, Any, Set, Callable
from collections import defaultdict
from dataclasses import dataclass, field

from ..types import LogRecord
from .buffer import SmartBuffer
from .context import Context


@dataclass
class AggregationRule:
    """Rule for log aggregation."""

    field: str  # Field to group by
    window: float  # Time window in seconds
    threshold: int  # Threshold for alerts
    callback: Optional[Callable[[List[LogRecord]], None]] = None


@dataclass
class AggregationMetrics:
    """Metrics for aggregated logs."""

    count: int = 0
    error_count: int = 0
    warning_count: int = 0
    avg_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0
    last_timestamp: float = 0.0
    unique_contexts: Set[str] = field(default_factory=set)


class LogAggregator:
    """Advanced log aggregator with real-time analysis."""

    def __init__(
        self,
        max_buffer_size: int = 1000000,
        max_window: float = 3600.0,  # 1 hour default
        check_interval: float = 1.0,
        compression_enabled: bool = True,
    ):
        """Initialize the log aggregator.

        Args:
            max_buffer_size: Maximum records in buffer
            max_window: Maximum aggregation window
            check_interval: Interval for rule checks
            compression_enabled: Whether to use compression
        """
        self.max_window = max_window
        self.check_interval = check_interval

        # Initialize smart buffer
        self.buffer = SmartBuffer(
            max_size=max_buffer_size,
            compression_threshold=10000 if compression_enabled else float("inf"),
        )

        # Initialize aggregation state
        self._rules: List[AggregationRule] = []
        self._metrics: Dict[str, AggregationMetrics] = defaultdict(AggregationMetrics)
        self._windows: Dict[str, Dict[float, List[LogRecord]]] = defaultdict(
            lambda: defaultdict(list)
        )

        # Threading state
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

        # Start background tasks
        self._start_background_tasks()

    def _start_background_tasks(self) -> None:
        """Start background maintenance tasks."""
        self._maintenance_thread = threading.Thread(
            target=self._maintenance_loop, daemon=True
        )
        self._maintenance_thread.start()

    def _maintenance_loop(self) -> None:
        """Background loop for maintenance tasks."""
        while not self._stop_event.is_set():
            try:
                self._check_rules()
                self._prune_old_windows()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"Error in aggregator maintenance: {e}")

    def add_rule(
        self,
        field: str,
        window: float,
        threshold: int,
        callback: Optional[Callable[[List[LogRecord]], None]] = None,
    ) -> None:
        """Add an aggregation rule.

        Args:
            field: Field to group by (dot notation supported)
            window: Time window in seconds
            threshold: Threshold for alerts
            callback: Optional callback for alerts
        """
        rule = AggregationRule(
            field=field,
            window=min(window, self.max_window),
            threshold=threshold,
            callback=callback,
        )
        self._rules.append(rule)

    def _get_field_value(self, record: LogRecord, field: str) -> Any:
        """Get a field value using dot notation."""
        parts = field.split(".")
        value = record
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = getattr(value, part, None)
            if value is None:
                break
        return value

    def _update_metrics(self, group: str, record: LogRecord) -> None:
        """Update metrics for a group."""
        metrics = self._metrics[group]
        metrics.count += 1
        metrics.last_timestamp = record.timestamp

        if hasattr(record, "level"):
            if record.level == "ERROR":
                metrics.error_count += 1
            elif record.level == "WARNING":
                metrics.warning_count += 1

        if hasattr(record, "latency"):
            # Update average latency
            metrics.avg_latency = (
                metrics.avg_latency * (metrics.count - 1) + record.latency
            ) / metrics.count

        if isinstance(record.context, Context):
            metrics.unique_contexts.add(str(record.context))

    def process_record(self, record: LogRecord) -> None:
        """Process a new log record.

        Args:
            record: LogRecord to process
        """
        # Add to buffer
        self.buffer.add_record(record)

        # Process aggregation rules
        with self._lock:
            for rule in self._rules:
                value = self._get_field_value(record, rule.field)
                if value is not None:
                    group = f"{rule.field}:{value}"
                    window_key = int(record.timestamp / rule.window) * rule.window
                    self._windows[group][window_key].append(record)
                    self._update_metrics(group, record)

    def _check_rules(self) -> None:
        """Check aggregation rules for threshold violations."""
        current_time = time.time()

        with self._lock:
            for rule in self._rules:
                for group, windows in self._windows.items():
                    if not group.startswith(f"{rule.field}:"):
                        continue

                    # Get records in current window
                    window_key = int(current_time / rule.window) * rule.window
                    window_records = windows.get(window_key, [])

                    if len(window_records) >= rule.threshold and rule.callback:
                        rule.callback(window_records)

    def _prune_old_windows(self) -> None:
        """Remove windows outside the maximum window."""
        current_time = time.time()

        with self._lock:
            for group, windows in self._windows.items():
                to_remove = []
                for window_key in windows:
                    if current_time - window_key > self.max_window:
                        to_remove.append(window_key)
                for key in to_remove:
                    del windows[key]

    def get_metrics(self, group: Optional[str] = None) -> Dict[str, AggregationMetrics]:
        """Get current metrics.

        Args:
            group: Optional group filter

        Returns:
            Dict mapping groups to metrics
        """
        with self._lock:
            if group:
                return {group: self._metrics[group]}
            return dict(self._metrics)

    def get_window(
        self, group: str, window_start: Optional[float] = None
    ) -> List[LogRecord]:
        """Get records for a specific window.

        Args:
            group: Group to get records for
            window_start: Optional window start time

        Returns:
            List of records in window
        """
        with self._lock:
            if window_start is None:
                window_start = int(time.time() / 60) * 60

            return self._windows[group].get(window_start, [])

    def shutdown(self) -> None:
        """Shutdown the aggregator."""
        self._stop_event.set()
        if self._maintenance_thread.is_alive():
            self._maintenance_thread.join(timeout=5.0)
        self.buffer.shutdown()
