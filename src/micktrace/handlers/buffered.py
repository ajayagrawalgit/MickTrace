"""Memory-efficient handler with smart buffering."""

from typing import Optional, Dict, Any, List, Callable
from ..core.buffer import SmartBuffer
from ..core.aggregator import LogAggregator
from ..types import LogRecord


class BufferedHandler:
    """Handler with smart buffering and aggregation."""

    def __init__(
        self,
        max_buffer_size: int = 1000000,
        compression_enabled: bool = True,
        max_window: float = 3600.0,
        callback: Optional[Callable[[List[LogRecord]], None]] = None,
    ):
        """Initialize the buffered handler.

        Args:
            max_buffer_size: Maximum records in buffer
            compression_enabled: Whether to use compression
            max_window: Maximum aggregation window
            callback: Optional callback for flushed records
        """
        self.buffer = SmartBuffer(
            max_size=max_buffer_size,
            compression_threshold=10000 if compression_enabled else float("inf"),
        )

        self.aggregator = LogAggregator(
            max_buffer_size=max_buffer_size, max_window=max_window
        )

        self.callback = callback

    def handle(self, record: LogRecord) -> None:
        """Handle a log record.

        Args:
            record: LogRecord to handle
        """
        # Add to buffer and aggregator
        self.buffer.add_record(record)
        self.aggregator.process_record(record)

    def add_aggregation_rule(
        self,
        field: str,
        window: float,
        threshold: int,
        callback: Optional[Callable[[List[LogRecord]], None]] = None,
    ) -> None:
        """Add an aggregation rule.

        Args:
            field: Field to group by
            window: Time window in seconds
            threshold: Threshold for alerts
            callback: Optional callback for alerts
        """
        self.aggregator.add_rule(field, window, threshold, callback)

    def get_metrics(self, group: Optional[str] = None) -> Dict[str, Any]:
        """Get current metrics.

        Args:
            group: Optional group filter

        Returns:
            Dict of metrics
        """
        return self.aggregator.get_metrics(group)

    def flush(self) -> None:
        """Flush buffered records."""
        # Flush all partitions
        flushed = self.buffer.flush_all()

        # Call callback if provided
        if self.callback and flushed:
            for records in flushed.values():
                self.callback(records)

    def shutdown(self) -> None:
        """Shutdown the handler."""
        self.flush()
        self.buffer.shutdown()
        self.aggregator.shutdown()
