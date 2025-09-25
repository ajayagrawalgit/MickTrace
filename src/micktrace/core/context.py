"""
Context Management System

Provides async-safe context propagation for structured logging.
Supports automatic injection of correlation IDs, user context, 
request metadata, and other structured data.
"""

import asyncio
import threading
from contextlib import contextmanager, asynccontextmanager
from contextvars import ContextVar, Token
from typing import Any, Dict, Optional, Iterator, AsyncIterator, Union
from uuid import uuid4


# Context variables for async-safe storage
_log_context: ContextVar[Dict[str, Any]] = ContextVar('log_context', default={})
_correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
_trace_id: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
_user_id: ContextVar[Optional[Union[str, int]]] = ContextVar('user_id', default=None)
_request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)

# Thread-local fallback for non-async environments
_thread_local = threading.local()


class ContextManager:
    """High-level context management with automatic cleanup."""

    def __init__(self) -> None:
        self._tokens: list[Token] = []

    def set(self, key: str, value: Any) -> None:
        """Set a context value."""
        current_context = self.get_all()
        new_context = current_context.copy()
        new_context[key] = value

        token = _log_context.set(new_context)
        self._tokens.append(token)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a context value."""
        context = _log_context.get({})
        return context.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        """Get all context data."""
        try:
            # Try async context first
            return _log_context.get({})
        except LookupError:
            # Fallback to thread-local storage
            return getattr(_thread_local, 'context', {})

    def update(self, data: Dict[str, Any]) -> None:
        """Update context with multiple values."""
        current_context = self.get_all()
        new_context = current_context.copy()
        new_context.update(data)

        token = _log_context.set(new_context)
        self._tokens.append(token)

    def clear(self) -> None:
        """Clear all context data."""
        token = _log_context.set({})
        self._tokens.append(token)

    def cleanup(self) -> None:
        """Reset all context variables to their previous values."""
        for token in reversed(self._tokens):
            _log_context.reset(token)
        self._tokens.clear()


def get_context() -> Dict[str, Any]:
    """Get the current logging context."""
    try:
        context = _log_context.get({}).copy()

        # Add special context variables if set
        correlation_id = _correlation_id.get()
        if correlation_id:
            context['correlation_id'] = correlation_id

        trace_id = _trace_id.get()  
        if trace_id:
            context['trace_id'] = trace_id

        user_id = _user_id.get()
        if user_id:
            context['user_id'] = user_id

        request_id = _request_id.get()
        if request_id:
            context['request_id'] = request_id

        return context

    except LookupError:
        # Fallback to thread-local storage
        thread_context = getattr(_thread_local, 'context', {})
        return thread_context.copy()


def set_context(**kwargs: Any) -> None:
    """Set context variables."""
    current_context = get_context()
    new_context = current_context.copy()
    new_context.update(kwargs)

    try:
        _log_context.set(new_context)
    except LookupError:
        # Fallback to thread-local storage
        _thread_local.context = new_context


def clear_context() -> None:
    """Clear all context data."""
    try:
        _log_context.set({})
        _correlation_id.set(None)
        _trace_id.set(None) 
        _user_id.set(None)
        _request_id.set(None)
    except LookupError:
        # Fallback to thread-local storage
        _thread_local.context = {}


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    try:
        return _correlation_id.get()
    except LookupError:
        return getattr(_thread_local, 'correlation_id', None)


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID."""
    try:
        _correlation_id.set(correlation_id)
    except LookupError:
        _thread_local.correlation_id = correlation_id


def get_trace_id() -> Optional[str]:
    """Get the current trace ID."""  
    try:
        return _trace_id.get()
    except LookupError:
        return getattr(_thread_local, 'trace_id', None)


def set_trace_id(trace_id: str) -> None:
    """Set the trace ID."""
    try:
        _trace_id.set(trace_id)
    except LookupError:
        _thread_local.trace_id = trace_id


def new_correlation_id() -> str:
    """Generate and set a new correlation ID."""
    correlation_id = str(uuid4())
    set_correlation_id(correlation_id)
    return correlation_id


def new_trace_id() -> str:
    """Generate and set a new trace ID."""
    trace_id = str(uuid4())
    set_trace_id(trace_id)
    return trace_id


@contextmanager
def context(**kwargs: Any) -> Iterator[None]:
    """Context manager for temporary context data.

    Example:
        with micktrace.context(user_id=123, request_id="req_456"):
            logger.info("User action")  # Includes user_id and request_id
    """
    ctx_manager = ContextManager()

    try:
        ctx_manager.update(kwargs)
        yield
    finally:
        ctx_manager.cleanup()


@asynccontextmanager
async def acontext(**kwargs: Any) -> AsyncIterator[None]:
    """Async context manager for temporary context data."""
    ctx_manager = ContextManager()

    try:
        ctx_manager.update(kwargs)
        yield
    finally:
        ctx_manager.cleanup()


@contextmanager 
def correlation(**kwargs: Any) -> Iterator[str]:
    """Context manager that generates a correlation ID.

    Example:
        with micktrace.correlation(user_id=123) as correlation_id:
            logger.info("Starting process")
            # All logs will include the correlation_id
    """
    correlation_id = new_correlation_id()

    with context(correlation_id=correlation_id, **kwargs):
        yield correlation_id


@asynccontextmanager
async def acorrelation(**kwargs: Any) -> AsyncIterator[str]:
    """Async context manager that generates a correlation ID."""
    correlation_id = new_correlation_id()

    async with acontext(correlation_id=correlation_id, **kwargs):
        yield correlation_id


@contextmanager
def trace(name: Optional[str] = None, **kwargs: Any) -> Iterator["TraceContext"]:
    """Context manager for tracing operations.

    Example:
        with micktrace.trace("database_query", table="users") as trace:
            result = db.query("SELECT * FROM users")
            trace.info(f"Found {len(result)} users")
    """
    trace_id = new_trace_id()
    trace_name = name or "trace"

    trace_context = TraceContext(trace_id, trace_name)

    with context(trace_id=trace_id, trace_name=trace_name, **kwargs):
        yield trace_context


@asynccontextmanager
async def atrace(name: Optional[str] = None, **kwargs: Any) -> AsyncIterator["TraceContext"]:
    """Async context manager for tracing operations."""
    trace_id = new_trace_id()
    trace_name = name or "trace"

    trace_context = TraceContext(trace_id, trace_name)

    async with acontext(trace_id=trace_id, trace_name=trace_name, **kwargs):
        yield trace_context


class TraceContext:
    """Context object provided by trace context managers."""

    def __init__(self, trace_id: str, name: str) -> None:
        self.trace_id = trace_id
        self.name = name
        self._start_time = None

    def start(self) -> None:
        """Start timing the trace."""
        import time
        self._start_time = time.time()

    def end(self) -> float:
        """End the trace and return duration."""
        if self._start_time is None:
            return 0.0

        import time
        duration = time.time() - self._start_time
        set_context(trace_duration=duration)
        return duration

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message within this trace."""
        from .logger import get_logger
        logger = get_logger("micktrace.trace")
        logger.info(message, trace_id=self.trace_id, trace_name=self.name, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message within this trace."""
        from .logger import get_logger
        logger = get_logger("micktrace.trace")
        logger.debug(message, trace_id=self.trace_id, trace_name=self.name, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message within this trace."""
        from .logger import get_logger
        logger = get_logger("micktrace.trace")
        logger.error(message, trace_id=self.trace_id, trace_name=self.name, **kwargs)


# Convenience functions for common patterns
def with_user(user_id: Union[str, int]) -> contextmanager:
    """Context manager for user-scoped logging."""
    return context(user_id=user_id)


def with_request(request_id: str, **kwargs: Any) -> contextmanager:
    """Context manager for request-scoped logging."""
    return context(request_id=request_id, **kwargs)


def with_service(service: str, version: Optional[str] = None, **kwargs: Any) -> contextmanager:
    """Context manager for service-scoped logging."""
    ctx_data = {"service": service}
    if version:
        ctx_data["version"] = version
    ctx_data.update(kwargs)
    return context(**ctx_data)
