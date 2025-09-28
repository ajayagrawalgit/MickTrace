"""Core Logger implementation with comprehensive error handling and zero circular dependencies."""

import asyncio
import datetime
import inspect
import sys
import threading
import time
import traceback
from typing import Any, Dict, List, Optional, Union, Awaitable

from ..types import LogLevel, LogRecord
from ..config.configuration import get_configuration
from .context import get_context
from ..handlers.handlers import FileHandler
from ..handlers.rotating import RotatingFileHandler
from ..handlers import ConsoleHandler, NullHandler, MemoryHandler

class Logger:
    """High-performance, async-native logger with structured logging support."""

    _loggers: Dict[str, "Logger"] = {}
    _library_loggers: Dict[str, "Logger"] = {}
    _handler_map: Dict[str, Any] = {
        'console': ConsoleHandler,
        'file': FileHandler,
        'null': NullHandler,
        'memory': MemoryHandler,
        'rotating_file': RotatingFileHandler
    }
    
    def __init__(self, name: str, handlers: Optional[List[Any]] = None, level: Union[str, LogLevel] = LogLevel.INFO):
        """Initialize a logger.
        
        Args:
            name: Logger name
            handlers: Optional list of handlers
            level: Minimum log level to process (default: INFO)
        """
        self.name = name
        self._handlers = handlers or []
        self.level = level if isinstance(level, LogLevel) else LogLevel.from_string(level)
        self._lock = threading.Lock()
        self._async_lock = asyncio.Lock()
        self._correlation_id: Optional[str] = None
        self._trace_id: Optional[str] = None
        """Initialize a logger.
        
        Args:
            name: Logger name
            handlers: Optional list of handlers
        """
        self.name = name
        self._handlers = handlers or []
        
    def add_handler(self, handler: Any) -> None:
        """Add a handler to the logger.
        
        Args:
            handler: Handler instance to add
        """
        self._handlers.append(handler)
        
    def remove_handler(self, handler: Any) -> None:
        """Remove a handler from the logger.
        
        Args:
            handler: Handler instance to remove
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
    
    def get_handlers(self) -> List[Any]:
        """Get all handlers attached to this logger.
        
        Returns:
            List of handlers
        """
        return self._handlers.copy()
        
    def clear_handlers(self) -> None:
        """Remove all handlers from this logger."""
        self._handlers.clear()
        
    @classmethod
    def get_logger(cls, name: str) -> "Logger":
        """Get a logger by name.
        
        Args:
            name: Logger name
            
        Returns:
            Logger instance
        """
        if name not in cls._loggers:
            cls._loggers[name] = cls(name)
        return cls._loggers[name]
        
    @classmethod
    def get_library_logger(cls, name: str) -> "Logger":
        """Get a library logger by name.
        
        Args:
            name: Logger name
            
        Returns:
            Logger instance
        """
        if name not in cls._library_loggers:
            cls._library_loggers[name] = cls(name)
        return cls._library_loggers[name]
            
    def _log(self, level: LogLevel, message: str, data: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None) -> None:
        """Internal method to handle log record creation and processing.
        
        Args:
            level: Log level
            message: Log message
            data: Optional structured data
            exc_info: Optional exception info
        """
        if level < self.level:
            return
            
        # Build exception info if provided
        exception = None
        if exc_info:
            exception = {
                'type': exc_info.__class__.__name__,
                'message': str(exc_info),
                'traceback': getattr(exc_info, '__traceback__', None)
            }

        # Get caller info
        frame = inspect.currentframe()
        caller = {}
        try:
            if frame:
                # Skip this frame and the public logging method frame
                frame = frame.f_back.f_back
                if frame:
                    caller = {
                        'file': frame.f_code.co_filename,
                        'function': frame.f_code.co_name,
                        'line': frame.f_lineno
                    }
        finally:
            del frame  # Avoid reference cycles
            
        record = LogRecord(
            timestamp=time.time(),
            level=level.name,
            logger_name=self.name,
            message=message,
            data=data or {},
            caller=caller,
            exception=exception,
            correlation_id=self._correlation_id,
            trace_id=self._trace_id
        )
        
        with self._lock:
            for handler in self._handlers:
                try:
                    handler.handle(record)
                except Exception as e:
                    print(f"Error in handler {handler}: {e}")
                    
    async def _async_log(self, level: LogLevel, message: str, data: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None) -> None:
        """Internal method to handle async log record creation and processing.
        
        Args:
            level: Log level
            message: Log message
            data: Optional structured data
            exc_info: Optional exception info
        """
        if level < self.level:
            return
            
        # Build exception info if provided
        exception = None
        if exc_info:
            exception = {
                'type': exc_info.__class__.__name__,
                'message': str(exc_info),
                'traceback': getattr(exc_info, '__traceback__', None)
            }

        # Get caller info
        frame = inspect.currentframe()
        caller = {}
        try:
            if frame:
                # Skip this frame and the public logging method frame
                frame = frame.f_back.f_back
                if frame:
                    caller = {
                        'file': frame.f_code.co_filename,
                        'function': frame.f_code.co_name,
                        'line': frame.f_lineno
                    }
        finally:
            del frame  # Avoid reference cycles
            
        record = LogRecord(
            timestamp=time.time(),
            level=level.name,
            logger_name=self.name,
            message=message,
            data=data or {},
            caller=caller,
            exception=exception,
            correlation_id=self._correlation_id,
            trace_id=self._trace_id
        )
        
        async with self._async_lock:
            for handler in self._handlers:
                try:
                    if hasattr(handler, 'async_handle'):
                        await handler.async_handle(record)
                    else:
                        handler.handle(record)
                except Exception as e:
                    print(f"Error in handler {handler}: {e}")
                    
    def debug(self, message: str, data: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None) -> None:
        """Log a debug message.
        
        Args:
            message: Log message
            data: Optional structured data
            exc_info: Optional exception info
        """
        self._log(LogLevel.DEBUG, message, data, exc_info)
        
    def info(self, message: str, data: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None) -> None:
        """Log an info message.
        
        Args:
            message: Log message
            data: Optional structured data
            exc_info: Optional exception info
        """
        self._log(LogLevel.INFO, message, data, exc_info)
        
    def warning(self, message: str, data: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None) -> None:
        """Log a warning message.
        
        Args:
            message: Log message
            data: Optional structured data
            exc_info: Optional exception info
        """
        self._log(LogLevel.WARNING, message, data, exc_info)
        
    def error(self, message: str, data: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None) -> None:
        """Log an error message.
        
        Args:
            message: Log message
            data: Optional structured data
            exc_info: Optional exception info
        """
        self._log(LogLevel.ERROR, message, data, exc_info)
        
    def critical(self, message: str, data: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None) -> None:
        """Log a critical message.
        
        Args:
            message: Log message
            data: Optional structured data
            exc_info: Optional exception info
        """
        self._log(LogLevel.CRITICAL, message, data, exc_info)
        
    async def async_debug(self, message: str, data: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None) -> None:
        """Asynchronously log a debug message.
        
        Args:
            message: Log message
            data: Optional structured data
            exc_info: Optional exception info
        """
        await self._async_log(LogLevel.DEBUG, message, data, exc_info)
        
    async def async_info(self, message: str, data: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None) -> None:
        """Asynchronously log an info message.
        
        Args:
            message: Log message
            data: Optional structured data
            exc_info: Optional exception info
        """
        await self._async_log(LogLevel.INFO, message, data, exc_info)
        
    async def async_warning(self, message: str, data: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None) -> None:
        """Asynchronously log a warning message.
        
        Args:
            message: Log message
            data: Optional structured data
            exc_info: Optional exception info
        """
        await self._async_log(LogLevel.WARNING, message, data, exc_info)
        
    async def async_error(self, message: str, data: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None) -> None:
        """Asynchronously log an error message.
        
        Args:
            message: Log message
            data: Optional structured data
            exc_info: Optional exception info
        """
        await self._async_log(LogLevel.ERROR, message, data, exc_info)
        
    async def async_critical(self, message: str, data: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None) -> None:
        """Asynchronously log a critical message.
        
        Args:
            message: Log message
            data: Optional structured data
            exc_info: Optional exception info
        """
        await self._async_log(LogLevel.CRITICAL, message, data, exc_info)
        
    def set_correlation_id(self, correlation_id: Optional[str]) -> None:
        """Set the correlation ID for this logger.
        
        Args:
            correlation_id: Correlation ID for distributed tracing
        """
        self._correlation_id = correlation_id
        
    def set_trace_id(self, trace_id: Optional[str]) -> None:
        """Set the trace ID for this logger.
        
        Args:
            trace_id: Trace ID for distributed tracing
        """
        self._trace_id = trace_id

    @classmethod
    def create_handler(cls, handler_type: str, handler_config: Dict[str, Any]) -> Any:
        """Create a handler instance from configuration."""
        handler_name = handler_config.get('name', handler_type)
        level = LogLevel.from_string(handler_config.get('level', 'INFO'))
        enabled = handler_config.get('enabled', True)

        # Skip disabled handlers
        if not enabled or handler_type not in cls._handler_map:
            return None
            
        # Build config - merge any remaining configs
        config = handler_config.copy()
        for key in ['type', 'name', 'level', 'enabled', 'format', 'filters', 'formatter']:
            config.pop(key, None)

        handler_class = cls._handler_map[handler_type]
        return handler_class(name=handler_name, level=level, **config)

    @classmethod
    def get(cls, name: str) -> "Logger":
        """Get or create a logger instance."""
        if not name or not isinstance(name, str):
            name = "root"
            
        is_library = any(name.startswith(lib) for lib in ['micktrace'])
        logger_store = cls._library_loggers if is_library else cls._loggers
        
        if name in logger_store:
            return logger_store[name]

        logger = cls(name, is_library=is_library)
        logger_store[name] = logger
        return logger

    def __init__(self, name: str, level: Optional[Union[str, LogLevel]] = None, 
                 is_library: bool = False, bound_data: Optional[Dict[str, Any]] = None) -> None:
        """Initialize a new logger instance."""
        self.name = str(name) if name else "unknown"
        self.is_library = bool(is_library)
        self._level = self._normalize_level(level) if level else LogLevel.NOTSET
        self._handlers: List[Any] = []
        self._filters: List[Any] = []  # Initialize filters list
        self._config_cache_time = 0.0
        self._cached_config = None
        self._cache_ttl = 1.0
        self._bound_data = bound_data or {}
        
        # Add context manager
        from .context import get_context
        self.context = get_context

        try:
            config = self._get_config()
            if hasattr(config, 'handlers'):
                for handler_config in config.handlers:
                    if isinstance(handler_config, dict):
                        handler = self.create_handler(handler_config.get('type', ''), handler_config)
                        if handler:
                            self._handlers.append(handler)
        except Exception:
            pass

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
            return LogLevel.INFO
        except Exception:
            return LogLevel.INFO

    def add_filter(self, filter_obj: Any) -> None:
        """Add a filter to the logger.
        
        Args:
            filter_obj: Filter object that implements should_sample(record) method
        """
        if hasattr(filter_obj, 'should_sample'):
            self._filters.append(filter_obj)
            
    def remove_filter(self, filter_obj: Any) -> None:
        """Remove a filter from the logger."""
        if filter_obj in self._filters:
            self._filters.remove(filter_obj)
            
    def _should_log(self, level: LogLevel) -> bool:
        """Check if we should log at the given level."""
        try:
            # Check basic logging conditions
            if self.is_library:
                config = self._get_config()
                if not getattr(config, 'is_configured', False):
                    return False

            config = self._get_config()
            if not getattr(config, 'enabled', True):
                return False

            effective_level = self._get_effective_level()
            if level < effective_level:
                return False
                
            return True
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

    def _emit_simple(self, record: LogRecord) -> None:
        """Simple emit for basic functionality."""
        try:
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
                                data_parts.append(f"{key}=<e>")
                    if data_parts:
                        parts.append(" ".join(data_parts))
                except Exception:
                    pass

            message = " ".join(parts)
            print(message)
        except Exception:
            try:
                record_message = getattr(record, 'message', 'error')
                fallback_msg = "LOG: " + str(record_message)
                print(fallback_msg)
            except Exception:
                pass

    def _log(self, level: LogLevel, message: str, exc_info: Optional[Union[bool, tuple, BaseException]] = None,
             **kwargs: Any) -> Optional[Awaitable[None]]:
        """Internal logging method."""
        try:
            if not self._should_log(level):
                return None

            record = self._create_record(level, message, kwargs, exc_info)
            
            # Apply filters
            for filter_obj in self._filters:
                try:
                    if not filter_obj.should_sample(record):
                        return None
                except Exception:
                    pass
            
            self._emit_simple(record)

            for handler in self._handlers:
                try:
                    handler.handle(record)
                except Exception:
                    pass

        except Exception:
            pass
        return None

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


def bind(**kwargs: Any) -> Logger:
    """Create a new logger with bound context."""
    return get_logger().bind(**kwargs)