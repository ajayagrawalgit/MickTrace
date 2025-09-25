"""
Performance monitoring utilities for micktrace.
"""

import time
import threading
from typing import Dict, Any, Optional


class Timer:
    """High-precision timer for performance measurement."""

    def __init__(self) -> None:
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

    def start(self) -> None:
        """Start timing."""
        self._start_time = time.perf_counter()

    def stop(self) -> float:
        """Stop timing and return duration."""
        if self._start_time is None:
            raise ValueError("Timer not started")

        self._end_time = time.perf_counter()
        return self._end_time - self._start_time

    def elapsed(self) -> float:
        """Get elapsed time without stopping."""
        if self._start_time is None:
            return 0.0
        return time.perf_counter() - self._start_time


class PerformanceCounter:
    """Thread-safe performance counter."""

    def __init__(self) -> None:
        self._counts: Dict[str, int] = {}
        self._times: Dict[str, float] = {}
        self._lock = threading.Lock()

    def increment(self, name: str, count: int = 1) -> None:
        """Increment a counter."""
        with self._lock:
            self._counts[name] = self._counts.get(name, 0) + count

    def add_time(self, name: str, duration: float) -> None:
        """Add time measurement."""
        with self._lock:
            self._times[name] = self._times.get(name, 0.0) + duration

    def get_stats(self) -> Dict[str, Any]:
        """Get all statistics."""
        with self._lock:
            return {
                "counts": self._counts.copy(),
                "times": self._times.copy()
            }

    def reset(self) -> None:
        """Reset all counters."""
        with self._lock:
            self._counts.clear()
            self._times.clear()
