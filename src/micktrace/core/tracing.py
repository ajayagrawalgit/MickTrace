"""
Tracing and Performance Monitoring

Provides high-performance timing, tracing, and performance monitoring
utilities with automatic context propagation and structured logging.
"""

import asyncio
import time
import threading
from contextlib import contextmanager, asynccontextmanager
from typing import Any, Dict, Optional, Union, Iterator, AsyncIterator, Callable
from uuid import uuid4
from dataclasses import dataclass, field

from .context import context, acontext


@dataclass
class TimingData:
    """Container for timing measurements."""
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self) -> float:
        """Mark the timing as finished and calculate duration."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        return self.duration

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        result = {
            "start_time": self.start_time,
            "duration": self.duration,
        }

        if self.name:
            result["name"] = self.name
        if self.end_time:
            result["end_time"] = self.end_time
        if self.metadata:
            result.update(self.metadata)

        return result


class Timer:
    """High-precision timer for performance measurement."""

    def __init__(self, name: Optional[str] = None) -> None:
        self.name = name
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._timings: list[TimingData] = []

    def start(self) -> None:
        """Start the timer."""
        self._start_time = self.now()

    def stop(self) -> float:
        """Stop the timer and return duration.""" 
        if self._start_time is None:
            raise ValueError("Timer not started")

        self._end_time = self.now()
        duration = self._end_time - self._start_time

        timing = TimingData(
            start_time=self._start_time,
            end_time=self._end_time,
            duration=duration,
            name=self.name
        )
        self._timings.append(timing)

        return duration

    def reset(self) -> None:
        """Reset the timer."""
        self._start_time = None
        self._end_time = None

    def elapsed(self) -> float:
        """Get elapsed time without stopping."""
        if self._start_time is None:
            return 0.0
        return self.now() - self._start_time

    @staticmethod
    def now() -> float:
        """Get current high-precision timestamp."""
        return time.perf_counter()

    def get_stats(self) -> Dict[str, Any]:
        """Get timing statistics."""
        if not self._timings:
            return {}

        durations = [t.duration for t in self._timings if t.duration is not None]
        if not durations:
            return {}

        return {
            "count": len(durations),
            "total": sum(durations),
            "average": sum(durations) / len(durations),
            "min": min(durations), 
            "max": max(durations)
        }

    def __enter__(self) -> "Timer":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


@contextmanager
def timer(name: Optional[str] = None, **metadata: Any) -> Iterator[Timer]:
    """Context manager for timing operations.

    Example:
        with micktrace.timer("database_query") as t:
            result = db.query("SELECT * FROM users")
            # Timing automatically logged
    """
    timer_obj = Timer(name)

    try:
        timer_obj.start()
        yield timer_obj
    finally:
        duration = timer_obj.stop()

        # Log the timing
        from .logger import get_logger
        logger = get_logger("micktrace.timer")

        log_data = {"duration": duration}
        if name:
            log_data["timer_name"] = name
        log_data.update(metadata)

        logger.info(f"Timer {name or 'unnamed'} completed", **log_data)


@asynccontextmanager
async def atimer(name: Optional[str] = None, **metadata: Any) -> AsyncIterator[Timer]:
    """Async context manager for timing operations."""
    timer_obj = Timer(name)

    try:
        timer_obj.start()
        yield timer_obj
    finally:
        duration = timer_obj.stop()

        # Log the timing
        from .logger import get_logger
        logger = get_logger("micktrace.timer")

        log_data = {"duration": duration}
        if name:
            log_data["timer_name"] = name
        log_data.update(metadata)

        logger.info(f"Timer {name or 'unnamed'} completed", **log_data)


class Tracer:
    """Advanced tracing with span support."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.trace_id = str(uuid4())
        self._spans: list[Dict[str, Any]] = []
        self._active_spans: Dict[str, TimingData] = {}

    def start_span(self, name: str, **metadata: Any) -> str:
        """Start a new span."""
        span_id = str(uuid4())

        timing = TimingData(
            start_time=time.perf_counter(),
            name=name,
            metadata=metadata
        )

        self._active_spans[span_id] = timing
        return span_id

    def end_span(self, span_id: str, **metadata: Any) -> float:
        """End a span."""
        if span_id not in self._active_spans:
            raise ValueError(f"Unknown span ID: {span_id}")

        timing = self._active_spans.pop(span_id)
        duration = timing.finish()

        # Add any additional metadata
        timing.metadata.update(metadata)

        # Store completed span
        span_data = timing.to_dict()
        span_data["span_id"] = span_id
        span_data["trace_id"] = self.trace_id
        self._spans.append(span_data)

        return duration

    def get_spans(self) -> list[Dict[str, Any]]:
        """Get all completed spans."""
        return self._spans.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Convert tracer to dictionary."""
        return {
            "trace_id": self.trace_id,
            "name": self.name,
            "spans": self.get_spans(),
            "span_count": len(self._spans)
        }


@contextmanager
def trace(name: str, **metadata: Any) -> Iterator[Tracer]:
    """Context manager for distributed tracing.

    Example:
        with micktrace.trace("request_processing") as tracer:
            span_id = tracer.start_span("database_query")
            result = db.query("SELECT * FROM users") 
            tracer.end_span(span_id, rows=len(result))
    """
    tracer = Tracer(name)

    with context(trace_id=tracer.trace_id, trace_name=name, **metadata):
        try:
            yield tracer
        finally:
            # Log trace summary
            from .logger import get_logger
            logger = get_logger("micktrace.trace")

            trace_data = tracer.to_dict()
            logger.info(f"Trace {name} completed", **trace_data)


@asynccontextmanager
async def atrace(name: str, **metadata: Any) -> AsyncIterator[Tracer]:
    """Async context manager for distributed tracing."""
    tracer = Tracer(name)

    async with acontext(trace_id=tracer.trace_id, trace_name=name, **metadata):
        try:
            yield tracer
        finally:
            # Log trace summary
            from .logger import get_logger
            logger = get_logger("micktrace.trace")

            trace_data = tracer.to_dict()
            logger.info(f"Trace {name} completed", **trace_data)


# Performance monitoring utilities
class PerformanceMonitor:
    """Monitor performance metrics over time."""

    def __init__(self) -> None:
        self._metrics: Dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def record(self, name: str, value: float) -> None:
        """Record a performance metric."""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = []
            self._metrics[name].append(value)

    def get_stats(self, name: str) -> Dict[str, Any]:
        """Get statistics for a metric."""
        with self._lock:
            values = self._metrics.get(name, [])

            if not values:
                return {}

            return {
                "count": len(values),
                "total": sum(values),
                "average": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "latest": values[-1] if values else None
            }

    def reset(self, name: Optional[str] = None) -> None:
        """Reset metrics."""
        with self._lock:
            if name:
                self._metrics.pop(name, None)
            else:
                self._metrics.clear()

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all metrics."""
        return {name: self.get_stats(name) for name in self._metrics}


# Global performance monitor
_performance_monitor = PerformanceMonitor()


def record_metric(name: str, value: float) -> None:
    """Record a performance metric globally."""
    _performance_monitor.record(name, value)


def get_metric_stats(name: str) -> Dict[str, Any]:
    """Get statistics for a performance metric."""
    return _performance_monitor.get_stats(name)


def get_all_metric_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all performance metrics."""
    return _performance_monitor.get_all_stats()


# Convenience functions
def now() -> float:
    """Get current high-precision timestamp."""
    return time.perf_counter()


def elapsed(start_time: float) -> float:
    """Calculate elapsed time from start timestamp."""
    return time.perf_counter() - start_time


# Decorator for automatic function timing
def timed(name: Optional[str] = None, log_args: bool = False) -> Callable:
    """Decorator to automatically time function calls.

    Example:
        @micktrace.timed("expensive_function")
        def process_data(data):
            # Function is automatically timed
            return processed_data
    """
    def decorator(func: Callable) -> Callable:
        func_name = name or f"{func.__module__}.{func.__name__}"

        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                start_time = now()

                log_data = {"function": func_name}
                if log_args:
                    log_data.update({
                        "args_count": len(args),
                        "kwargs_count": len(kwargs)
                    })

                try:
                    result = await func(*args, **kwargs)
                    duration = elapsed(start_time)

                    from .logger import get_logger
                    logger = get_logger("micktrace.timed")
                    logger.info(f"Function {func_name} completed", 
                               duration=duration, **log_data)

                    record_metric(f"function.{func_name}.duration", duration)
                    return result

                except Exception as e:
                    duration = elapsed(start_time)

                    from .logger import get_logger
                    logger = get_logger("micktrace.timed")
                    logger.error(f"Function {func_name} failed",
                                duration=duration, error=str(e), **log_data)

                    record_metric(f"function.{func_name}.error_duration", duration)
                    raise

            return async_wrapper

        else:
            def sync_wrapper(*args, **kwargs):
                start_time = now()

                log_data = {"function": func_name}
                if log_args:
                    log_data.update({
                        "args_count": len(args),
                        "kwargs_count": len(kwargs)
                    })

                try:
                    result = func(*args, **kwargs)
                    duration = elapsed(start_time)

                    from .logger import get_logger
                    logger = get_logger("micktrace.timed")
                    logger.info(f"Function {func_name} completed",
                               duration=duration, **log_data)

                    record_metric(f"function.{func_name}.duration", duration)
                    return result

                except Exception as e:
                    duration = elapsed(start_time)

                    from .logger import get_logger  
                    logger = get_logger("micktrace.timed")
                    logger.error(f"Function {func_name} failed",
                                duration=duration, error=str(e), **log_data)

                    record_metric(f"function.{func_name}.error_duration", duration)
                    raise

            return sync_wrapper

    return decorator
