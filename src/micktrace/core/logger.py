"""
Core Logger implementation with zero circular imports and perfect error handling.
"""

import inspect
import sys
import time
import traceback
from typing import Any, Dict, List, Optional, Union, Awaitable

from ..types import LogLevel, LogRecord
from ..config.configuration import get_configuration
from .context import get_context


class Logger:
    """High-performance, async-native logger with structured logging support."""

    _loggers: Dict[str, "Logger"] = {}
    _library_loggers: Dict[str, "Logger"] = {}

    def __init__(self, name: str, level: Optional[Union[str, LogLevel]] = None, is_library: bool = False) -> None:
        self.name = str(name) if name else "unknown"
        self.is_library = bool(is_library)
        self._level = self._normalize_level(level) if level else LogLevel.NOTSET
        self._handlers: List[Any] = []
        self._config_cache_time = 0.0
        self._cached_config = None
        self._cache_ttl = 1.0

    @classmethod
    def get(cls, name: str) -> "Logger":
        """Get or create a logger instance with error handling."""
        try:
            if not name or not isinstance(name, str):
                name = "root"
            if name not in cls._loggers:
                cls._loggers[name] = cls(name)
            return cls._loggers[name]
        except Exception:
            return cls("error_logger")

    @classmethod 
    def for_library(cls, name: str) -> "Logger":
        """Get a library-safe logger."""
        try:
            if not name or not isinstance(name, str):
                name = "library"
            if name not in cls._library_loggers:
                cls._library_loggers[name] = cls(name, is_library=True)
            return cls._library_loggers[name]
        except Exception:
            return cls("library_error", is_library=True)

    def _get_config(self):
        """Get configuration with caching for performance."""
        try:
            current_time = time.time()
            if self._cached_config is None or current_time - self._config_cache_time > self._cache_ttl:
                self._cached_config = get_configuration()
                self._config_cache_time = current_time
            return self._cached_config
        except Exception:
            class FallbackConfig:
                level = "INFO"
                is_configured = False
                enabled = True
            return FallbackConfig()

    def _normalize_level(self, level: Union[str, LogLevel, int]) -> LogLevel:
        """Normalize level input to LogLevel enum."""
        try:
            if isinstance(level, LogLevel):
                return level
            elif isinstance(level, str):
                return LogLevel.from_string(level)
            elif isinstance(level, int):
                for log_level in LogLevel:
                    if log_level.value == level:
                        return log_level
                closest = min(LogLevel, key=lambda x: abs(x.value - level))
                return closest
            else:
                return LogLevel.INFO
        except Exception:
            return LogLevel.INFO

    def _should_log(self, level: LogLevel) -> bool:
        """Check if we should log at the given level."""
        try:
            if self.is_library:
                config = self._get_config()
                if not getattr(config, 'is_configured', False):
                    return False

            config = self._get_config()
            if not getattr(config, 'enabled', True):
                return False

            effective_level = self._get_effective_level()
            return level >= effective_level
        except Exception:
            return level >= LogLevel.ERROR

    def _get_effective_level(self) -> LogLevel:
        """Get the effective logging level."""
        try:
            if self._level != LogLevel.NOTSET:
                return self._level
            config = self._get_config()
            config_level = getattr(config, 'level', 'INFO')
            return LogLevel.from_string(config_level)
        except Exception:
            return LogLevel.INFO

    def _get_caller_info(self) -> Dict[str, Any]:
        """Get information about the calling code."""
        caller_info = {"filename": "unknown", "lineno": 0, "function": "unknown", "module": "unknown"}

        try:
            frame = inspect.currentframe()
            stack_depth = 0

            while frame and stack_depth < 20:
                try:
                    filename = frame.f_code.co_filename
                    skip_patterns = ["micktrace", "logger.py", "context.py"]
                    if not any(pattern in filename for pattern in skip_patterns):
                        import os
                        basename = os.path.basename(filename)
                        caller_info.update({
                            "filename": basename,
                            "lineno": frame.f_lineno,
                            "function": frame.f_code.co_name,
                            "module": frame.f_globals.get("__name__", "unknown")
                        })
                        break
                    frame = frame.f_back
                    stack_depth += 1
                except Exception:
                    break
        except Exception:
            pass

        return caller_info

    def _create_record(self, level: LogLevel, message: str, extra: Optional[Dict[str, Any]] = None, 
                      exc_info: Optional[Union[bool, tuple, BaseException]] = None) -> LogRecord:
        """Create a log record."""
        try:
            now = time.time()

            try:
                caller_info = self._get_caller_info()
            except Exception:
                caller_info = {}

            try:
                context_data = get_context()
            except Exception:
                context_data = {}

            data = {}
            try:
                if context_data and isinstance(context_data, dict):
                    data.update(context_data)
                if extra and isinstance(extra, dict):
                    data.update(extra)
            except Exception:
                data = extra if extra and isinstance(extra, dict) else {}

            exception_data = None
            if exc_info:
                try:
                    if exc_info is True:
                        exc_info = sys.exc_info()

                    if isinstance(exc_info, BaseException):
                        exception_data = {"type": type(exc_info).__name__, "message": str(exc_info)}
                    elif isinstance(exc_info, tuple) and len(exc_info) == 3:
                        exc_type, exc_value, exc_traceback = exc_info
                        if exc_type and exc_value:
                            exception_data = {"type": exc_type.__name__, "message": str(exc_value)}
                except Exception:
                    exception_data = {"error": "Failed to process exception info"}

            return LogRecord(
                timestamp=now,
                level=level.name,
                logger_name=self.name,
                message=str(message),
                data=data,
                caller=caller_info,
                exception=exception_data
            )

        except Exception:
            return LogRecord(
                timestamp=time.time(),
                level=getattr(level, 'name', 'INFO'),
                logger_name=self.name,
                message=str(message) if message else "Error creating log record",
                data={},
                caller={},
                exception=None
            )

    def _log(self, level: LogLevel, message: str, exc_info: Optional[Union[bool, tuple, BaseException]] = None, 
             **kwargs: Any) -> Optional[Awaitable[None]]:
        """Internal logging method."""
        try:
            if not self._should_log(level):
                return None
            record = self._create_record(level, message, kwargs, exc_info)
            self._emit_simple(record)
        except Exception:
            pass
        return None

    def _emit_simple(self, record: LogRecord) -> None:
        """Simple emit for basic functionality."""
        try:
            from datetime import datetime
            try:
                dt = datetime.fromtimestamp(record.timestamp)
                timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                timestamp_str = str(record.timestamp)

            parts = [timestamp_str, f"[{record.level:>8}]", record.logger_name, record.message]

            if record.data:
                try:
                    data_parts = []
                    for key, value in record.data.items():
                        if key != 'timestamp_iso':
                            try:
                                data_parts.append(f"{key}={value}")
                            except Exception:
                                data_parts.append(f"{key}=<error>")
                    if data_parts:
                        parts.append(" ".join(data_parts))
                except Exception:
                    pass

            message = " ".join(parts)
            print(message)
        except Exception:
            try:
                # Fixed: Use string concatenation instead of complex f-string
                record_message = getattr(record, 'message', 'error')
                fallback_msg = "LOG: " + str(record_message)
                print(fallback_msg)
            except Exception:
                pass

    def debug(self, message: str, exc_info: Optional[Union[bool, tuple, BaseException]] = None, **kwargs: Any) -> Optional[Awaitable[None]]:
        """Log a DEBUG level message."""
        try:
            return self._log(LogLevel.DEBUG, message, exc_info, **kwargs)
        except Exception:
            return None

    def info(self, message: str, exc_info: Optional[Union[bool, tuple, BaseException]] = None, **kwargs: Any) -> Optional[Awaitable[None]]:
        """Log an INFO level message."""
        try:
            return self._log(LogLevel.INFO, message, exc_info, **kwargs)
        except Exception:
            return None

    def warning(self, message: str, exc_info: Optional[Union[bool, tuple, BaseException]] = None, **kwargs: Any) -> Optional[Awaitable[None]]:
        """Log a WARNING level message."""
        try:
            return self._log(LogLevel.WARNING, message, exc_info, **kwargs)
        except Exception:
            return None

    def error(self, message: str, exc_info: Optional[Union[bool, tuple, BaseException]] = None, **kwargs: Any) -> Optional[Awaitable[None]]:
        """Log an ERROR level message."""
        try:
            return self._log(LogLevel.ERROR, message, exc_info, **kwargs)
        except Exception:
            return None

    def critical(self, message: str, exc_info: Optional[Union[bool, tuple, BaseException]] = None, **kwargs: Any) -> Optional[Awaitable[None]]:
        """Log a CRITICAL level message."""
        try:
            return self._log(LogLevel.CRITICAL, message, exc_info, **kwargs)
        except Exception:
            return None

    def exception(self, message: str, **kwargs: Any) -> Optional[Awaitable[None]]:
        """Log an ERROR level message with exception info."""
        try:
            return self.error(message, exc_info=True, **kwargs)
        except Exception:
            return None

    warn = warning
    fatal = critical

    def set_level(self, level: Union[str, LogLevel, int]) -> None:
        """Set the logging level for this logger."""
        try:
            self._level = self._normalize_level(level)
        except Exception:
            self._level = LogLevel.INFO

    def get_level(self) -> LogLevel:
        """Get the current logging level."""
        try:
            return self._get_effective_level()
        except Exception:
            return LogLevel.INFO

    def is_enabled_for(self, level: Union[str, LogLevel, int]) -> bool:
        """Check if logging is enabled for the given level."""
        try:
            normalized_level = self._normalize_level(level)
            return self._should_log(normalized_level)
        except Exception:
            return False

    def bind(self, **kwargs: Any) -> "BoundLogger":
        """Create a bound logger with additional context."""
        try:
            return BoundLogger(self, kwargs)
        except Exception:
            return BoundLogger(self, {})

    def __repr__(self) -> str:
        try:
            level = self._get_effective_level()
            return f"<Logger {self.name} ({level.name})>"
        except Exception:
            return f"<Logger {self.name}>"


class BoundLogger:
    """A logger bound with additional context data."""

    def __init__(self, logger: Logger, context: Dict[str, Any]) -> None:
        self._logger = logger if isinstance(logger, Logger) else Logger("bound_error")
        self._context = context if isinstance(context, dict) else {}

    def _merge_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge bound context with method kwargs."""
        try:
            merged = self._context.copy()
            if isinstance(kwargs, dict):
                merged.update(kwargs)
            return merged
        except Exception:
            return kwargs if isinstance(kwargs, dict) else {}

    def debug(self, message: str, **kwargs: Any) -> Optional[Awaitable[None]]:
        try:
            return self._logger.debug(message, **self._merge_kwargs(kwargs))
        except Exception:
            return None

    def info(self, message: str, **kwargs: Any) -> Optional[Awaitable[None]]:
        try:
            return self._logger.info(message, **self._merge_kwargs(kwargs))
        except Exception:
            return None

    def warning(self, message: str, **kwargs: Any) -> Optional[Awaitable[None]]:
        try:
            return self._logger.warning(message, **self._merge_kwargs(kwargs))
        except Exception:
            return None

    def error(self, message: str, **kwargs: Any) -> Optional[Awaitable[None]]:
        try:
            return self._logger.error(message, **self._merge_kwargs(kwargs))
        except Exception:
            return None

    def critical(self, message: str, **kwargs: Any) -> Optional[Awaitable[None]]:
        try:
            return self._logger.critical(message, **self._merge_kwargs(kwargs))
        except Exception:
            return None

    def exception(self, message: str, **kwargs: Any) -> Optional[Awaitable[None]]:
        try:
            return self._logger.exception(message, **self._merge_kwargs(kwargs))
        except Exception:
            return None

    warn = warning
    fatal = critical

    def bind(self, **kwargs: Any) -> "BoundLogger":
        """Create a new bound logger with additional context."""
        try:
            return BoundLogger(self._logger, self._merge_kwargs(kwargs))
        except Exception:
            return self

    def __repr__(self) -> str:
        try:
            return f"<BoundLogger {self._logger.name} with {len(self._context)} bound fields>"
        except Exception:
            return "<BoundLogger>"


def get_logger(name: Optional[str] = None) -> Logger:
    """Get a logger instance with error handling."""
    try:
        if name is None:
            try:
                frame = inspect.currentframe()
                if frame and frame.f_back:
                    name = frame.f_back.f_globals.get("__name__", "root")
                else:
                    name = "root"
            except Exception:
                name = "root"
        return Logger.get(name)
    except Exception:
        return Logger("fallback")
