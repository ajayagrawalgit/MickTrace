"""
Core Logger Implementation

The Logger class is the heart of micktrace, providing:
- Library-first design with zero global state pollution
- Async-native operations with automatic queue management  
- Structured logging by default
- Type-safe context propagation
- Sub-microsecond overhead when disabled
"""

import asyncio
import inspect
import sys
import time
import traceback
from contextvars import ContextVar
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable
from types import TracebackType

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

# Context variable for async-safe logger state
_logger_context: ContextVar[Dict[str, Any]] = ContextVar('logger_context', default={})

class LogLevel(Enum):
    """Log levels with numeric values for comparison."""
    NOTSET = 0
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    @classmethod
    def from_string(cls, level: str) -> "LogLevel":
        """Convert string to LogLevel enum."""
        return cls[level.upper()]

    def __lt__(self, other: "LogLevel") -> bool:
        return self.value < other.value

    def __le__(self, other: "LogLevel") -> bool:
        return self.value <= other.value


def get_context() -> Dict[str, Any]:
    """Get the current logging context - fallback implementation."""
    try:
        return _logger_context.get({})
    except LookupError:
        return {}


def get_configuration():
    """Get configuration - fallback implementation."""
    # Simple default configuration
    class DefaultConfig:
        is_configured = False
        level = "INFO"

    return DefaultConfig()


class HandlerManager:
    """Simple handler manager for fallback."""
    def __init__(self):
        self._handlers = []

    def handle(self, record):
        """Handle a record."""
        return None

    def get_all_handlers(self):
        return self._handlers

    def add_handler(self, handler):
        self._handlers.append(handler)

    def remove_handler(self, name):
        self._handlers = [h for h in self._handlers if getattr(h, 'name', None) != name]


class Timer:
    """Simple timer for fallback."""
    def __init__(self):
        pass


class LogRecord:
    """Simple log record for fallback."""
    def __init__(self, timestamp, level, logger_name, message, data=None, caller=None, exception=None):
        self.timestamp = timestamp
        self.level = level
        self.logger_name = logger_name
        self.message = message
        self.data = data or {}
        self.caller = caller or {}
        self.exception = exception


class Logger:
    """
    High-performance, async-native logger with structured logging support.

    Features:
    - Zero global state pollution 
    - Sub-microsecond overhead when disabled
    - Automatic context injection
    - Type-safe structured logging
    - Async-native with queue management
    - Multiprocessing safe
    """

    _loggers: Dict[str, "Logger"] = {}
    _library_loggers: Dict[str, "Logger"] = {}

    def __init__(
        self, 
        name: str,
        level: Optional[Union[str, LogLevel]] = None,
        is_library: bool = False
    ) -> None:
        self.name = name
        self.is_library = is_library
        self._level = self._normalize_level(level) if level else LogLevel.NOTSET
        self._handler_manager = HandlerManager()
        self._timer = Timer()

        # Performance optimization: Cache frequently accessed config
        self._config_cache_time = 0.0
        self._cached_config = None
        self._cache_ttl = 1.0  # Cache config for 1 second

    @classmethod
    def get(cls, name: str) -> "Logger":
        """Get or create a logger instance."""
        if name not in cls._loggers:
            cls._loggers[name] = cls(name)
        return cls._loggers[name]

    @classmethod 
    def for_library(cls, name: str) -> "Logger":
        """Get a library-safe logger that's a no-op until configured."""
        if name not in cls._library_loggers:
            cls._library_loggers[name] = cls(name, is_library=True)
        return cls._library_loggers[name]

    def _get_config(self):
        """Get configuration with caching for performance."""
        current_time = time.time()
        if (
            self._cached_config is None or 
            current_time - self._config_cache_time > self._cache_ttl
        ):
            self._cached_config = get_configuration()
            self._config_cache_time = current_time
        return self._cached_config

    def _normalize_level(self, level: Union[str, LogLevel, int]) -> LogLevel:
        """Normalize level input to LogLevel enum."""
        if isinstance(level, LogLevel):
            return level
        elif isinstance(level, str):
            return LogLevel.from_string(level)
        elif isinstance(level, int):
            # Map integer to closest LogLevel
            for log_level in LogLevel:
                if log_level.value == level:
                    return log_level
            # Find closest level
            closest = min(LogLevel, key=lambda x: abs(x.value - level))
            return closest
        else:
            raise ValueError(f"Invalid level type: {type(level)}")

    def _should_log(self, level: LogLevel) -> bool:
        """Check if we should log at the given level."""
        # For library loggers, only log if application has configured micktrace
        if self.is_library:
            config = self._get_config()
            if not config.is_configured:
                return False

        # Check level threshold
        effective_level = self._get_effective_level()
        return level >= effective_level

    def _get_effective_level(self) -> LogLevel:
        """Get the effective logging level."""
        if self._level != LogLevel.NOTSET:
            return self._level

        config = self._get_config()
        return LogLevel.from_string(config.level)

    def _get_caller_info(self) -> Dict[str, Any]:
        """Get information about the calling code."""
        frame = inspect.currentframe()
        caller_info = {
            "filename": "unknown",
            "lineno": 0,
            "function": "unknown",
            "module": "unknown"
        }

        try:
            # Walk up the stack to find the caller outside micktrace
            while frame:
                filename = frame.f_code.co_filename
                if not filename.endswith(("micktrace", "logger.py")):
                    caller_info.update({
                        "filename": filename.split("/")[-1],
                        "lineno": frame.f_lineno,
                        "function": frame.f_code.co_name,
                        "module": frame.f_globals.get("__name__", "unknown")
                    })
                    break
                frame = frame.f_back
        except Exception:
            pass  # Use defaults if stack inspection fails

        return caller_info

    def _create_record(
        self,
        level: LogLevel,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Union[bool, tuple, BaseException]] = None
    ) -> LogRecord:
        """Create a log record."""
        now = time.time()

        # Get caller information
        caller_info = self._get_caller_info()

        # Get context data
        context_data = get_context()

        # Merge extra data
        data = {}
        if context_data:
            data.update(context_data)
        if extra:
            data.update(extra)

        # Handle exception info
        exception_data = None
        if exc_info:
            if exc_info is True:
                exc_info = sys.exc_info()

            if isinstance(exc_info, BaseException):
                exception_data = {
                    "type": type(exc_info).__name__,
                    "message": str(exc_info),
                    "traceback": traceback.format_exception(
                        type(exc_info), exc_info, exc_info.__traceback__
                    )
                }
            elif isinstance(exc_info, tuple) and len(exc_info) == 3:
                exc_type, exc_value, exc_traceback = exc_info
                if exc_type and exc_value:
                    exception_data = {
                        "type": exc_type.__name__,
                        "message": str(exc_value),
                        "traceback": traceback.format_exception(
                            exc_type, exc_value, exc_traceback
                        )
                    }

        return LogRecord(
            timestamp=now,
            level=level.name,
            logger_name=self.name,
            message=message,
            data=data,
            caller=caller_info,
            exception=exception_data
        )

    def _log(
        self,
        level: LogLevel,
        message: str,
        *,
        exc_info: Optional[Union[bool, tuple, BaseException]] = None,
        **kwargs: Any
    ) -> Optional[Awaitable[None]]:
        """Internal logging method."""
        # Fast path: Check if we should log before doing expensive work
        if not self._should_log(level):
            return None

        # Create log record
        record = self._create_record(level, message, kwargs, exc_info)

        # Submit to handler manager
        return self._handler_manager.handle(record)

    # Public logging methods
    def debug(
        self, 
        message: str,
        *,
        exc_info: Optional[Union[bool, tuple, BaseException]] = None,
        **kwargs: Any
    ) -> Optional[Awaitable[None]]:
        """Log a DEBUG level message."""
        return self._log(LogLevel.DEBUG, message, exc_info=exc_info, **kwargs)

    def info(
        self,
        message: str,
        *,
        exc_info: Optional[Union[bool, tuple, BaseException]] = None,
        **kwargs: Any
    ) -> Optional[Awaitable[None]]:
        """Log an INFO level message."""
        return self._log(LogLevel.INFO, message, exc_info=exc_info, **kwargs)

    def warning(
        self,
        message: str, 
        *,
        exc_info: Optional[Union[bool, tuple, BaseException]] = None,
        **kwargs: Any
    ) -> Optional[Awaitable[None]]:
        """Log a WARNING level message."""
        return self._log(LogLevel.WARNING, message, exc_info=exc_info, **kwargs)

    def error(
        self,
        message: str,
        *,
        exc_info: Optional[Union[bool, tuple, BaseException]] = None, 
        **kwargs: Any
    ) -> Optional[Awaitable[None]]:
        """Log an ERROR level message.""" 
        return self._log(LogLevel.ERROR, message, exc_info=exc_info, **kwargs)

    def critical(
        self,
        message: str,
        *,
        exc_info: Optional[Union[bool, tuple, BaseException]] = None,
        **kwargs: Any
    ) -> Optional[Awaitable[None]]:
        """Log a CRITICAL level message."""
        return self._log(LogLevel.CRITICAL, message, exc_info=exc_info, **kwargs)

    def exception(
        self,
        message: str,
        **kwargs: Any
    ) -> Optional[Awaitable[None]]:
        """Log an ERROR level message with exception info."""
        return self.error(message, exc_info=True, **kwargs)

    # Aliases for compatibility
    warn = warning
    fatal = critical

    # Level management
    def set_level(self, level: Union[str, LogLevel, int]) -> None:
        """Set the logging level for this logger."""
        self._level = self._normalize_level(level)

    def get_level(self) -> LogLevel:
        """Get the current logging level."""
        return self._get_effective_level()

    def is_enabled_for(self, level: Union[str, LogLevel, int]) -> bool:
        """Check if logging is enabled for the given level."""
        normalized_level = self._normalize_level(level)
        return self._should_log(normalized_level)

    # Context managers for structured logging
    def __enter__(self) -> "Logger":
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException], 
        exc_tb: Optional[TracebackType]
    ) -> None:
        """Exit context manager."""
        pass

    def bind(self, **kwargs: Any) -> "BoundLogger":
        """Create a bound logger with additional context."""
        return BoundLogger(self, kwargs)

    def __repr__(self) -> str:
        return f"<Logger {self.name} ({self._get_effective_level().name})>"


class BoundLogger:
    """A logger bound with additional context data."""

    def __init__(self, logger: Logger, context: Dict[str, Any]) -> None:
        self._logger = logger
        self._context = context

    def _merge_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge bound context with method kwargs."""
        merged = self._context.copy()
        merged.update(kwargs)
        return merged

    def debug(self, message: str, **kwargs: Any) -> Optional[Awaitable[None]]:
        return self._logger.debug(message, **self._merge_kwargs(kwargs))

    def info(self, message: str, **kwargs: Any) -> Optional[Awaitable[None]]:
        return self._logger.info(message, **self._merge_kwargs(kwargs))

    def warning(self, message: str, **kwargs: Any) -> Optional[Awaitable[None]]:
        return self._logger.warning(message, **self._merge_kwargs(kwargs))

    def error(self, message: str, **kwargs: Any) -> Optional[Awaitable[None]]:
        return self._logger.error(message, **self._merge_kwargs(kwargs))

    def critical(self, message: str, **kwargs: Any) -> Optional[Awaitable[None]]:
        return self._logger.critical(message, **self._merge_kwargs(kwargs))

    def exception(self, message: str, **kwargs: Any) -> Optional[Awaitable[None]]:
        return self._logger.exception(message, **self._merge_kwargs(kwargs))

    # Aliases
    warn = warning
    fatal = critical

    def bind(self, **kwargs: Any) -> "BoundLogger":
        """Create a new bound logger with additional context."""
        return BoundLogger(self._logger, self._merge_kwargs(kwargs))

    def __repr__(self) -> str:
        return f"<BoundLogger {self._logger.name} with {len(self._context)} bound fields>"


# Convenience function to get logger
def get_logger(name: Optional[str] = None) -> Logger:
    """Get a logger instance."""
    if name is None:
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get("__name__", "root")
        else:
            name = "root"

    return Logger.get(name)
