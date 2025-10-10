"""Smart log sampling system for MickTrace."""

import random
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Set
from ..types import LogRecord


@dataclass
class SamplingRule:
    """Definition of a sampling rule."""

    name: str
    rate: float  # Base sampling rate (0.0 to 1.0)
    # Optional condition to apply rule
    condition: Optional[Callable[[LogRecord], bool]] = None
    adaptive: bool = False  # Whether to use adaptive sampling
    error_boost: float = 2.0  # Multiply sampling rate by this much for error records
    max_rate: float = 1.0  # Maximum sampling rate for adaptive sampling
    min_rate: float = 0.01  # Minimum sampling rate for adaptive sampling


class AdaptiveSampler:
    """Implements adaptive sampling based on error rates and importance."""

    def __init__(self, window_size: int = 1000, error_threshold: float = 0.1):
        """Initialize the adaptive sampler.

        Args:
            window_size: Number of records to consider for error rate calculation
            error_threshold: Error rate threshold that triggers increased sampling
        """
        self.window_size = window_size
        self.error_threshold = error_threshold
        self.error_count = 0
        self.total_count = 0
        self._lock = threading.Lock()

    def record_error(self, is_error: bool) -> None:
        """Record whether a log was an error."""
        with self._lock:
            if self.total_count >= self.window_size:
                # Reset counters when window is full
                self.error_count = 0
                self.total_count = 0

            self.total_count += 1
            if is_error:
                self.error_count += 1

    def get_error_rate(self) -> float:
        """Get the current error rate."""
        with self._lock:
            if self.total_count == 0:
                return 0.0
            return self.error_count / self.total_count

    def get_sampling_rate(
        self, base_rate: float, min_rate: float, max_rate: float
    ) -> float:
        """Calculate the adaptive sampling rate based on error rate."""
        error_rate = self.get_error_rate()

        if error_rate >= self.error_threshold:
            # Increase sampling rate based on how much we exceed the threshold
            factor = 1.0 + ((error_rate - self.error_threshold) / self.error_threshold)
            return min(max_rate, base_rate * factor)

        return max(min_rate, base_rate)


class SmartSampler:
    """Intelligent log sampler with adaptive rates and consistent sampling."""

    def __init__(self):
        """Initialize the sampler."""
        self.rules: Dict[str, SamplingRule] = {}
        self.adaptive_samplers: Dict[str, AdaptiveSampler] = {}
        self.sampled_ids: Set[str] = set()  # For consistent sampling
        self._lock = threading.Lock()

    def add_rule(self, rule: SamplingRule) -> None:
        """Add a sampling rule.

        Example:
            sampler.add_rule(SamplingRule(
                name="debug_logs",
                rate=0.1,
                condition=lambda r: r.level == "DEBUG",
                adaptive=True
            ))
        """
        with self._lock:
            self.rules[rule.name] = rule
            if rule.adaptive:
                self.adaptive_samplers[rule.name] = AdaptiveSampler()

    def remove_rule(self, name: str) -> None:
        """Remove a sampling rule."""
        with self._lock:
            self.rules.pop(name, None)
            self.adaptive_samplers.pop(name, None)

    def _get_correlation_id(self, record: LogRecord) -> Optional[str]:
        """Extract correlation ID from record context."""
        if record.data:
            return str(record.data.get("correlation_id", ""))
        return None

    def _is_error(self, record: LogRecord) -> bool:
        """Check if the record is an error."""
        return record.level in ("ERROR", "CRITICAL")

    def should_sample(self, record: LogRecord) -> bool:
        """Determine if a log record should be sampled.

        Args:
            record: The log record to check

        Returns:
            bool: Whether the record should be sampled
        """
        # Always sample errors if no rules match
        if not self.rules and self._is_error(record):
            return True

        # Check correlation ID for consistent sampling
        correlation_id = self._get_correlation_id(record)
        if correlation_id and correlation_id in self.sampled_ids:
            return True

        # Find matching rules
        matched_rule = None
        for rule in self.rules.values():
            if rule.condition is None or rule.condition(record):
                matched_rule = rule
                break

        if matched_rule is None:
            # No matching rules - sample errors, drop others
            return self._is_error(record)

        # Get base sampling rate
        rate = matched_rule.rate

        # Apply error boost if applicable
        if self._is_error(record):
            rate = min(1.0, rate * matched_rule.error_boost)

        # Apply adaptive sampling if enabled
        if matched_rule.adaptive:
            sampler = self.adaptive_samplers[matched_rule.name]
            rate = sampler.get_sampling_rate(
                rate, matched_rule.min_rate, matched_rule.max_rate
            )

        # Make sampling decision
        should_sample = random.random() < rate

        # Update adaptive sampler stats
        if matched_rule.adaptive:
            sampler = self.adaptive_samplers[matched_rule.name]
            sampler.record_error(self._is_error(record))

        # Record correlation ID if sampling
        if should_sample and correlation_id:
            self.sampled_ids.add(correlation_id)

        # Clean up old correlation IDs periodically
        if len(self.sampled_ids) > 10000:  # Arbitrary cleanup threshold
            self.sampled_ids.clear()

        return should_sample
