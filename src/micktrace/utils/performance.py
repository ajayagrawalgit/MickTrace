"""Performance monitoring utilities for MickTrace."""

import asyncio
import functools
import time
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from contextvars import ContextVar

from ..core.logger import Logger
from ..types import F

# Type variables for better type hints
T = TypeVar("T")

# Context variables for tracking nested operations
_operation_stack: ContextVar[list[str]] = ContextVar("operation_stack", default=[])


class Timer:
    """Context manager and decorator for timing code execution.

    Example:
        # As a context manager
        with Timer(logger, "database_query"):
            result = db.execute(query)

        # As a decorator
        @Timer(logger, "process_data")
        def process_data(items):
            for item in items:
                process_item(item)
    """

    def __init__(
        self,
        logger: Logger,
        operation: str,
        extra_context: Optional[Dict[str, Any]] = None,
        threshold_ms: Optional[float] = None,
        include_args: bool = False,
    ):
        """Initialize the timer.

        Args:
            logger: Logger instance to use
            operation: Name of the operation being timed
            extra_context: Additional context to include in log messages
            threshold_ms: Only log if execution time exceeds this threshold
            include_args: Whether to include function arguments in logs
        """
        self.logger = logger
        self.operation = operation
        self.extra_context = extra_context or {}
        self.threshold_ms = threshold_ms
        self.include_args = include_args
        self.start_time: float = 0
        self.end_time: float = 0

    def _get_operation_path(self) -> str:
        """Get the full operation path including parent operations."""
        try:
            stack = _operation_stack.get()
            return ".".join(stack + [self.operation])
        except LookupError:
            return self.operation

    def _should_log(self, duration_ms: float) -> bool:
        """Check if the operation should be logged based on threshold."""
        return self.threshold_ms is None or duration_ms >= self.threshold_ms

    def _log_operation(
        self,
        status: str,
        duration_ms: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log operation details."""
        context = self.extra_context.copy()
        context.update({"operation": self._get_operation_path(), "status": status})

        if duration_ms is not None:
            context["duration_ms"] = duration_ms

        if extra:
            context.update(extra)

        if status == "completed":
            self.logger.info(f"Operation {self.operation} completed", **context)
        elif status == "error":
            self.logger.error(f"Operation {self.operation} failed", **context)
        else:
            self.logger.info(f"Operation {self.operation} {status}", **context)

    def __enter__(self) -> "Timer":
        """Start timing when entering the context."""
        try:
            stack = _operation_stack.get()
            stack.append(self.operation)
            _operation_stack.set(stack)
        except LookupError:
            _operation_stack.set([self.operation])

        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop timing when exiting the context and log results."""
        self.end_time = time.perf_counter()
        duration_ms = (self.end_time - self.start_time) * 1000

        try:
            stack = _operation_stack.get()
            stack.pop()
            _operation_stack.set(stack)
        except (LookupError, IndexError):
            pass

        if exc_type is not None:
            # Log error with exception details
            self._log_operation(
                "error",
                duration_ms,
                {"error_type": exc_type.__name__, "error_message": str(exc_val)},
            )
        elif self._should_log(duration_ms):
            # Log successful completion
            self._log_operation("completed", duration_ms)

    def __call__(self, func: F) -> F:
        """Decorator interface for timing functions."""

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            extra = {}
            if self.include_args:
                extra.update({"args": args, "kwargs": kwargs})

            with Timer(
                self.logger,
                self.operation,
                {**self.extra_context, **extra},
                self.threshold_ms,
            ):
                return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            extra = {}
            if self.include_args:
                extra.update({"args": args, "kwargs": kwargs})

            with Timer(
                self.logger,
                self.operation,
                {**self.extra_context, **extra},
                self.threshold_ms,
            ):
                return await func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def track_memory(logger: Logger, operation: str) -> Callable[[F], F]:
    """Decorator to track memory usage of a function.

    Example:
        @track_memory(logger, "process_large_dataset")
        def process_large_dataset(data):
            # Process data here
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                import psutil

                process = psutil.Process()
                mem_before = process.memory_info().rss / 1024 / 1024  # MB

                result = func(*args, **kwargs)

                mem_after = process.memory_info().rss / 1024 / 1024  # MB
                mem_diff = mem_after - mem_before

                logger.info(
                    f"Memory usage for {operation}",
                    operation=operation,
                    memory_before_mb=mem_before,
                    memory_after_mb=mem_after,
                    memory_diff_mb=mem_diff,
                )

                return result

            except ImportError:
                logger.warning(
                    "psutil not installed, memory tracking disabled",
                    operation=operation,
                )
                return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                import psutil

                process = psutil.Process()
                mem_before = process.memory_info().rss / 1024 / 1024  # MB

                result = await func(*args, **kwargs)

                mem_after = process.memory_info().rss / 1024 / 1024  # MB
                mem_diff = mem_after - mem_before

                logger.info(
                    f"Memory usage for {operation}",
                    operation=operation,
                    memory_before_mb=mem_before,
                    memory_after_mb=mem_after,
                    memory_diff_mb=mem_diff,
                )

                return result

            except ImportError:
                logger.warning(
                    "psutil not installed, memory tracking disabled",
                    operation=operation,
                )
                return await func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper

    return decorator
