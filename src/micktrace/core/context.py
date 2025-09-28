"""
Context management system for micktrace.
Provides async-safe context propagation with comprehensive error handling.
"""

import asyncio
import threading
from contextlib import contextmanager, asynccontextmanager
from contextvars import ContextVar, Token
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Union, Iterator, AsyncIterator
from uuid import uuid4

class ContextProvider:
    """Dynamic context provider that can inject context based on runtime conditions."""
    
    def __init__(self, provider_func: Callable[[], Dict[str, Any]], refresh_interval: Optional[float] = None):
        """Initialize a context provider.
        
        Args:
            provider_func: Function that returns a dict of context values
            refresh_interval: How often to refresh the context (in seconds), or None for every call
        """
        self.provider_func = provider_func
        self.refresh_interval = refresh_interval
        self._last_refresh = 0
        self._cache: Dict[str, Any] = {}
        
    def get_context(self) -> Dict[str, Any]:
        """Get the current context from the provider."""
        import time
        current_time = time.time()
        
        if (self.refresh_interval is None or 
            current_time - self._last_refresh > self.refresh_interval):
            try:
                self._cache = self.provider_func()
                self._last_refresh = current_time
            except Exception as e:
                self._cache = {"provider_error": str(e)}
        
        return deepcopy(self._cache)


# Context variables for async-safe storage
_log_context: ContextVar[Dict[str, Any]] = ContextVar('log_context', default={})
_correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
_trace_id: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
_context_providers: Dict[str, ContextProvider] = {}

# Thread-local fallback for non-async environments
_thread_local = threading.local()


def _merge_contexts(base: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two context dictionaries."""
    result = deepcopy(base)
    
    def merge_dict(d1: Dict[str, Any], d2: Dict[str, Any]) -> None:
        for k, v in d2.items():
            if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
                merge_dict(d1[k], v)
            else:
                d1[k] = deepcopy(v)
                
    merge_dict(result, new)
    return result

def get_context() -> Dict[str, Any]:
    """Get the current logging context with comprehensive error handling."""
    try:
        # Try async context first
        context = _log_context.get({})
        if context is None:
            context = {}

        # Make a safe copy and merge provider contexts
        result = deepcopy(context) if isinstance(context, dict) else {}
        
        # Add provider contexts
        for name, provider in _context_providers.items():
            try:
                provider_context = provider.get_context()
                if provider_context:
                    result[name] = provider_context
            except Exception as e:
                result[f"{name}_error"] = str(e)

        # Add special context variables if set
        try:
            correlation_id = _correlation_id.get()
            if correlation_id:
                result['correlation_id'] = correlation_id
        except LookupError:
            pass

        try:
            trace_id = _trace_id.get()
            if trace_id:
                result['trace_id'] = trace_id
        except LookupError:
            pass

        return result

    except LookupError:
        # Fallback to thread-local storage
        try:
            thread_context = getattr(_thread_local, 'context', {})
            if not isinstance(thread_context, dict):
                thread_context = {}

            result = thread_context.copy()

            # Add thread-local correlation and trace IDs
            correlation_id = getattr(_thread_local, 'correlation_id', None)
            if correlation_id:
                result['correlation_id'] = correlation_id

            trace_id = getattr(_thread_local, 'trace_id', None)
            if trace_id:
                result['trace_id'] = trace_id

            return result

        except Exception:
            # Ultimate fallback
            return {}

    except Exception:
        # Ultimate fallback for any other error
        return {}


def set_context(**kwargs: Any) -> None:
    """Set context variables with error handling."""
    if not kwargs:
        return

    try:
        current_context = get_context()
        new_context = current_context.copy()
        new_context.update(kwargs)

        try:
            _log_context.set(new_context)
        except LookupError:
            # Fallback to thread-local storage
            _thread_local.context = new_context

    except Exception:
        # If all else fails, try thread-local
        try:
            if not hasattr(_thread_local, 'context'):
                _thread_local.context = {}
            _thread_local.context.update(kwargs)
        except Exception:
            # Silent failure - context is non-critical
            pass


def clear_context() -> None:
    """Clear all context data with error handling."""
    try:
        _log_context.set({})
        _correlation_id.set(None)
        _trace_id.set(None)
    except LookupError:
        # Fallback to thread-local storage
        try:
            _thread_local.context = {}
            _thread_local.correlation_id = None
            _thread_local.trace_id = None
        except Exception:
            pass
    except Exception:
        # Thread-local fallback
        try:
            _thread_local.context = {}
        except Exception:
            pass


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID with error handling."""
    try:
        return _correlation_id.get()
    except LookupError:
        try:
            return getattr(_thread_local, 'correlation_id', None)
        except Exception:
            return None
    except Exception:
        return None


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID with error handling."""
    if not correlation_id or not isinstance(correlation_id, str):
        return

    try:
        _correlation_id.set(correlation_id)
    except LookupError:
        try:
            _thread_local.correlation_id = correlation_id
        except Exception:
            pass
    except Exception:
        try:
            _thread_local.correlation_id = correlation_id
        except Exception:
            pass


def get_trace_id() -> Optional[str]:
    """Get the current trace ID with error handling."""
    try:
        return _trace_id.get()
    except LookupError:
        try:
            return getattr(_thread_local, 'trace_id', None)
        except Exception:
            return None
    except Exception:
        return None


def set_trace_id(trace_id: str) -> None:
    """Set the trace ID with error handling."""
    if not trace_id or not isinstance(trace_id, str):
        return

    try:
        _trace_id.set(trace_id)
    except LookupError:
        try:
            _thread_local.trace_id = trace_id
        except Exception:
            pass
    except Exception:
        try:
            _thread_local.trace_id = trace_id
        except Exception:
            pass


def new_correlation_id() -> str:
    """Generate and set a new correlation ID with error handling."""
    try:
        correlation_id = str(uuid4())
        set_correlation_id(correlation_id)
        return correlation_id
    except Exception:
        # Fallback correlation ID
        import time
        fallback_id = f"corr_{int(time.time() * 1000)}"
        set_correlation_id(fallback_id)
        return fallback_id


def new_trace_id() -> str:
    """Generate and set a new trace ID with error handling."""
    try:
        trace_id = str(uuid4())
        set_trace_id(trace_id)
        return trace_id
    except Exception:
        # Fallback trace ID
        import time
        fallback_id = f"trace_{int(time.time() * 1000)}"
        set_trace_id(fallback_id)
        return fallback_id


class ContextManager:
    """Context manager with automatic cleanup and error handling."""

    def __init__(self) -> None:
        self._tokens: List[Token] = []
        self._original_context: Optional[Dict[str, Any]] = None
        self._original_correlation: Optional[str] = None
        self._original_trace: Optional[str] = None

    def __enter__(self) -> "ContextManager":
        """Enter context manager with error handling."""
        try:
            # Save original state
            self._original_context = get_context()
            self._original_correlation = get_correlation_id()
            self._original_trace = get_trace_id()
        except Exception:
            # Initialize with empty state if saving fails
            self._original_context = {}
            self._original_correlation = None
            self._original_trace = None

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager with error handling."""
        try:
            # Restore original state
            if self._original_context is not None:
                try:
                    _log_context.set(self._original_context)
                except LookupError:
                    try:
                        _thread_local.context = self._original_context
                    except Exception:
                        pass

            if self._original_correlation is not None:
                set_correlation_id(self._original_correlation)
            elif self._original_correlation is None:
                try:
                    _correlation_id.set(None)
                except LookupError:
                    try:
                        _thread_local.correlation_id = None
                    except Exception:
                        pass

            if self._original_trace is not None:
                set_trace_id(self._original_trace)
            elif self._original_trace is None:
                try:
                    _trace_id.set(None)
                except LookupError:
                    try:
                        _thread_local.trace_id = None
                    except Exception:
                        pass

        except Exception:
            # If restoration fails, at least try to clear
            try:
                clear_context()
            except Exception:
                pass

    def set(self, **kwargs: Any) -> None:
        """Set context variables."""
        set_context(**kwargs)


@contextmanager
def context(**kwargs: Any) -> Iterator[None]:
    """Context manager for temporary context data with error handling."""
    ctx_manager = ContextManager()
    with ctx_manager:
        try:
            ctx_manager.set(**kwargs)
        except Exception:
            pass
        yield


@asynccontextmanager
async def acontext(**kwargs: Any) -> AsyncIterator[None]:
    """Async context manager for temporary context data with error handling."""
    ctx_manager = ContextManager()
    with ctx_manager:
        try:
            ctx_manager.set(**kwargs)
        except Exception:
            pass
        yield


@contextmanager
def correlation(**kwargs: Any) -> Iterator[str]:
    """Context manager that generates a correlation ID with error handling."""
    correlation_id = new_correlation_id()

    try:
        with context(correlation_id=correlation_id, **kwargs):
            yield correlation_id
    except Exception:
        yield correlation_id


@asynccontextmanager
async def acorrelation(**kwargs: Any) -> AsyncIterator[str]:
    """Async context manager that generates a correlation ID with error handling."""
    correlation_id = new_correlation_id()

    try:
        async with acontext(correlation_id=correlation_id, **kwargs):
            yield correlation_id
    except Exception:
        yield correlation_id
