"""
Context management system for micktrace.
Provides async-safe context propagation with comprehensive error handling.
"""

__all__ = [
    "ContextProvider",
    "DynamicContext",
    "Context",
    "get_context",
    "set_context",
    "clear_context",
    "context",
    "acontext",
    "correlation",
    "acorrelation",
]

import asyncio
import threading
import time
from contextlib import contextmanager, asynccontextmanager
from contextvars import ContextVar, Token
from copy import deepcopy
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    Iterator,
    AsyncIterator,
    TypeVar,
    Callable,
)
from dataclasses import dataclass, field
from uuid import uuid4

T = TypeVar("T")

# Global context variable for async-safe context propagation
_context_var: ContextVar[Dict[str, Any]] = ContextVar("micktrace_context", default={})


def get_context() -> Dict[str, Any]:
    """Get the current context data (async-safe)."""
    try:
        return _context_var.get().copy()
    except LookupError:
        return {}


def set_context(data: Dict[str, Any]) -> Token:
    """Set context data (async-safe). Returns token for restoration."""
    try:
        current = _context_var.get().copy()
        current.update(data)
        return _context_var.set(current)
    except Exception:
        return _context_var.set(data.copy())


def clear_context() -> None:
    """Clear all context data (async-safe)."""
    try:
        _context_var.set({})
    except Exception:
        pass


def new_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid4())


@dataclass
class DynamicContext:
    """Dynamic context that can have values populated at runtime."""

    def __init__(self, **providers: Callable[[], Any]) -> None:
        """Initialize with value providers.

        Args:
            **providers: Dict mapping field names to functions that return their values
        """
        self._providers = providers

    def get_values(self) -> Dict[str, Any]:
        """Get current values from all providers."""
        values = {}
        for key, provider in self._providers.items():
            try:
                values[key] = provider()
            except Exception:
                # If provider fails, skip this value
                continue
        return values


@dataclass
class ContextProvider:
    """Provides context data from various sources with error handling."""

    name: str
    provider: Callable[[], Dict[str, Any]]
    refresh_interval: float = 0.0
    enabled: bool = True
    _last_refresh: float = field(default=0.0, init=False)
    _cached_data: Dict[str, Any] = field(default_factory=dict, init=False)

    def get_data(self) -> Dict[str, Any]:
        """Get context data, using cache if refresh interval not exceeded."""
        if not self.enabled:
            return {}

        try:
            current_time = time.time()

            # Check if we need to refresh
            if (
                self.refresh_interval <= 0
                or current_time - self._last_refresh >= self.refresh_interval
            ):

                try:
                    self._cached_data = self.provider()
                    self._last_refresh = current_time
                except Exception:
                    # If provider fails, return cached data or empty dict
                    pass

            return self._cached_data.copy()

        except Exception:
            return {}


class Context:
    """Context manager for temporary context data with error handling."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize context with data."""
        self.data = kwargs
        self.token: Optional[Token] = None
        self.previous_context: Dict[str, Any] = {}

    def __enter__(self) -> "Context":
        """Enter context and set data."""
        try:
            self.previous_context = get_context()
            self.token = set_context(self.data)
        except Exception:
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and restore previous data."""
        try:
            if self.token is not None:
                _context_var.reset(self.token)
            else:
                clear_context()
        except Exception:
            pass

    async def __aenter__(self) -> "Context":
        """Enter async context."""
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        self.__exit__(exc_type, exc_val, exc_tb)


class ContextManager:
    """Advanced context manager with provider support."""

    def __init__(self) -> None:
        """Initialize context manager."""
        self._providers: Dict[str, ContextProvider] = {}
        self._permanent_context: Dict[str, Any] = {}
        self._lock = threading.RLock()

    def add_provider(
        self,
        name: str,
        provider: Callable[[], Dict[str, Any]],
        refresh_interval: float = 0.0,
    ) -> None:
        """Add a context provider."""
        try:
            with self._lock:
                self._providers[name] = ContextProvider(
                    name=name, provider=provider, refresh_interval=refresh_interval
                )
        except Exception:
            pass

    def remove_provider(self, name: str) -> None:
        """Remove a context provider."""
        try:
            with self._lock:
                self._providers.pop(name, None)
        except Exception:
            pass

    def bind_permanent(self, **kwargs: Any) -> None:
        """Add permanent context data."""
        try:
            with self._lock:
                self._permanent_context.update(kwargs)
        except Exception:
            pass

    def get_full_context(self) -> Dict[str, Any]:
        """Get full context including providers and permanent data."""
        try:
            context = {}

            # Add permanent context
            context.update(self._permanent_context)

            # Add provider data
            with self._lock:
                for provider in self._providers.values():
                    try:
                        provider_data = provider.get_data()
                        context.update(provider_data)
                    except Exception:
                        continue

            # Add current context
            context.update(get_context())

            return context

        except Exception:
            return get_context()

    def __enter__(self) -> "ContextManager":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        pass


@contextmanager
def context(**kwargs: Any) -> Iterator[None]:
    """Context manager for temporary context data with error handling."""
    ctx_manager = Context(**kwargs)
    try:
        with ctx_manager:
            yield
    except Exception:
        pass


@contextmanager
def correlation(**kwargs: Any) -> Iterator[str]:
    """Context manager that generates a correlation ID with error handling."""
    correlation_id = new_correlation_id()
    ctx_data = {"correlation_id": correlation_id}
    ctx_data.update(kwargs)

    try:
        with context(**ctx_data):
            yield correlation_id
    except Exception:
        yield correlation_id


@asynccontextmanager
async def acontext(**kwargs: Any) -> AsyncIterator[None]:
    """Async context manager for temporary context data with error handling."""
    ctx_manager = Context(**kwargs)
    try:
        async with ctx_manager:
            yield
    except Exception:
        pass


@asynccontextmanager
async def acorrelation(**kwargs: Any) -> AsyncIterator[str]:
    """Async context manager that generates a correlation ID with error handling."""
    correlation_id = new_correlation_id()
    ctx_data = {"correlation_id": correlation_id}
    ctx_data.update(kwargs)

    try:
        async with acontext(**ctx_data):
            yield correlation_id
    except Exception:
        yield correlation_id
