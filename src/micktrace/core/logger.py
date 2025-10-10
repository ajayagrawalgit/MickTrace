"""Core Logger implementation with comprehensive error handling."""

import inspect
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Awaitable

from ..types import LogLevel, LogRecord
from ..config.configuration import get_configuration
from .context import get_context


class Logger:
    """High-performance logger with structured logging support."""

    _loggers: Dict[str, "Logger"] = {}
    _library_loggers: Dict[str, "Logger"] = {}

    def __init__(
        self,
        name: str,
        level: Optional[Union[str, LogLevel]] = None,
        is_library: bool = False,
        bound_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a new logger instance."""
        self.name = str(name) if name else "unknown"
        self.is_library = bool(is_library)
        self._level = self._normalize_level(level) if level else LogLevel.NOTSET
        self._handlers: List[Any] = []
        self._filters: List[Any] = []
        self._config_cache_time = 0.0
        self._cached_config = None
        self._cache_ttl = 1.0
        self._bound_data = bound_data or {}
        self.context = get_context
        try:
            config = self._get_config()
            if hasattr(config, "handlers") and config.handlers:
                for handler_config in config.handlers:
                    try:
                        if hasattr(handler_config, "type"):
                            handler = self._create_handler_from_config(handler_config)
                            if handler:
                                self._handlers.append(handler)
                        elif isinstance(handler_config, dict):
                            handler = self._create_handler_from_dict(handler_config)
                            if handler:
                                self._handlers.append(handler)
                    except Exception:
                        continue
        except Exception:
            pass

    def add_handler(self, handler: Any) -> None:
        """Add a handler to the logger."""
        self._handlers.append(handler)

    def remove_handler(self, handler: Any) -> None:
        """Remove a handler from the logger."""
        if handler in self._handlers:
            self._handlers.remove(handler)

    def get_handlers(self) -> List[Any]:
        """Get all handlers attached to this logger."""
        return self._handlers.copy()

    def clear_handlers(self) -> None:
        """Remove all handlers from this logger."""
        self._handlers.clear()

    @classmethod
    def get(cls, name: str) -> "Logger":
        """Get or create a logger instance."""
        if not name or not isinstance(name, str):
            name = "root"
        is_library = any(name.startswith(lib) for lib in ["micktrace"])
        logger_store = cls._library_loggers if is_library else cls._loggers
        if name in logger_store:
            return logger_store[name]
        logger = cls(name, is_library=is_library)
        logger_store[name] = logger
        return logger

    def _get_config(self):
        """Get configuration with caching for performance."""
        try:
            current_time = time.time()
            if (
                self._cached_config is None
                or current_time - self._config_cache_time > self._cache_ttl
            ):
                self._cached_config = get_configuration()
                self._config_cache_time = current_time
            return self._cached_config
        except Exception:

            class FallbackConfig:
                level = "INFO"
                is_configured = False
                enabled = True
                handlers = []

            return FallbackConfig()

    def _create_handler_from_config(self, handler_config) -> Any:
        """Create a handler from HandlerConfig object."""
        try:
            handler_type = handler_config.type
            level = handler_config.level
            config = handler_config.config.copy() if handler_config.config else {}
            if handler_type == "file":
                from ..handlers.handlers import FileHandler

                if "path" in config:
                    path = config["path"]
                elif "config" in config and isinstance(config["config"], dict):
                    path = config["config"].get("path", "micktrace.log")
                else:
                    path = "micktrace.log"
                return FileHandler(filename=path, level=level)
            elif handler_type == "console":
                from ..handlers.console import ConsoleHandler

                return ConsoleHandler(level=level)
            elif handler_type == "null":
                from ..handlers.console import NullHandler

                return NullHandler(level=level)
            elif handler_type == "memory":
                from ..handlers.console import MemoryHandler

                return MemoryHandler(level=level)
            elif handler_type == "rotating":
                from ..handlers.rotating import RotatingFileHandler

                path = config.get("path", "micktrace.log")
                max_bytes = config.get("max_bytes", 10485760)  # 10MB
                backup_count = config.get("backup_count", 5)
                return RotatingFileHandler(
                    filename=path,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    level=level,
                )
            elif handler_type == "cloudwatch":
                try:
                    from ..handlers.cloudwatch import CloudWatchHandler

                    return CloudWatchHandler(
                        log_group_name=config.get("log_group", "micktrace"),
                        log_stream_name=config.get("log_stream", "default"),
                        region=config.get("region", "us-east-1"),
                    )
                except ImportError:
                    return None
            elif handler_type == "azure":
                try:
                    from ..handlers.azure import AzureMonitorHandler

                    return AzureMonitorHandler(
                        connection_string=config.get("connection_string", "")
                    )
                except ImportError:
                    return None
            elif handler_type == "stackdriver":
                try:
                    from ..handlers.stackdriver import StackdriverHandler

                    return StackdriverHandler(
                        project_id=config.get("project_id", ""),
                        log_name=config.get("log_name", "micktrace"),
                    )
                except ImportError:
                    return None
            elif handler_type == "datadog":
                try:
                    from ..handlers.datadog import DatadogHandler

                    return DatadogHandler(api_key=config.get("api_key"), dd_site=config.get("dd_site", "datadoghq.com"), level=level)
                except ImportError:
                    return None
            else:
                return None
        except Exception:
            return None

    def _create_handler_from_dict(self, handler_config: Dict[str, Any]) -> Any:
        """Create a handler from dictionary config."""
        try:
            handler_type = handler_config.get("type", "console")
            level = handler_config.get("level", "INFO")
            config = handler_config.get("config", {})
            if handler_type == "file":
                from ..handlers.handlers import FileHandler

                path = config.get("path", handler_config.get("path", "micktrace.log"))
                if (
                    path == "micktrace.log"
                    and "config" in config
                    and isinstance(config["config"], dict)
                ):
                    path = config["config"].get("path", "micktrace.log")
                return FileHandler(filename=path, level=level)
            elif handler_type == "console":
                from ..handlers.console import ConsoleHandler

                return ConsoleHandler(level=level)
            elif handler_type == "null":
                from ..handlers.console import NullHandler

                return NullHandler(level=level)
            elif handler_type == "memory":
                from ..handlers.console import MemoryHandler

                return MemoryHandler(level=level)
            elif handler_type == "rotating":
                from ..handlers.rotating import RotatingFileHandler

                path = config.get("path", handler_config.get("path", "micktrace.log"))
                max_bytes = config.get("max_bytes", 10485760)  # 10MB
                backup_count = config.get("backup_count", 5)
                return RotatingFileHandler(
                    filename=path,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    level=level,
                )
            elif handler_type == "cloudwatch":
                try:
                    from ..handlers.cloudwatch import CloudWatchHandler

                    return CloudWatchHandler(
                        log_group_name=config.get(
                            "log_group", handler_config.get("log_group", "micktrace")
                        ),
                        log_stream_name=config.get(
                            "log_stream", handler_config.get("log_stream", "default")
                        ),
                        region=config.get(
                            "region", handler_config.get("region", "us-east-1")
                        ),
                    )
                except ImportError:
                    return None
            elif handler_type == "azure":
                try:
                    from ..handlers.azure import AzureMonitorHandler

                    return AzureMonitorHandler(
                        connection_string=config.get(
                            "connection_string",
                            handler_config.get("connection_string", ""),
                        )
                    )
                except ImportError:
                    return None
            elif handler_type == "stackdriver":
                try:
                    from ..handlers.stackdriver import StackdriverHandler

                    return StackdriverHandler(
                        project_id=config.get(
                            "project_id", handler_config.get("project_id", "")
                        ),
                        log_name=config.get(
                            "log_name", handler_config.get("log_name", "micktrace")
                        ),
                    )
                except ImportError:
                    return None
            elif handler_type == "datadog":
                try:
                    from ..handlers.datadog import DatadogHandler

                    return DatadogHandler(api_key=config.get("api_key"), dd_site=config.get("dd_site", "datadoghq.com"), level=level)
                except ImportError:
                    return None
            else:
                return None
        except Exception:
            return None

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
        """Add a filter to the logger."""
        if hasattr(filter_obj, "should_sample"):
            self._filters.append(filter_obj)

    def remove_filter(self, filter_obj: Any) -> None:
        """Remove a filter from the logger."""
        if filter_obj in self._filters:
            self._filters.remove(filter_obj)

    def _should_log(self, level: LogLevel) -> bool:
        """Check if we should log at the given level."""
        try:
            if self.is_library:
                config = self._get_config()
                if not getattr(config, "is_configured", False):
                    return False
            config = self._get_config()
            if not getattr(config, "enabled", True):
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
            config_level = getattr(config, "level", "INFO")
            return LogLevel.from_string(config_level)
        except Exception:
            return LogLevel.INFO

    def _get_caller_info(self) -> Dict[str, Any]:
        """Get information about the calling code."""
        caller_info = {
            "filename": "unknown",
            "lineno": 0,
            "function": "unknown",
            "module": "unknown",
        }
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
                        caller_info.update(
                            {
                                "filename": basename,
                                "lineno": frame.f_lineno,
                                "function": frame.f_code.co_name,
                                "module": frame.f_globals.get("__name__", "unknown"),
                            }
                        )
                        break
                    frame = frame.f_back
                    stack_depth += 1
                except Exception:
                    break
        except Exception:
            pass
        return caller_info

    def _create_record(
        self,
        level: LogLevel,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Union[bool, tuple, BaseException]] = None,
    ) -> LogRecord:
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
                        exception_data = {
                            "type": type(exc_info).__name__,
                            "message": str(exc_info),
                        }
                    elif isinstance(exc_info, tuple) and len(exc_info) == 3:
                        exc_type, exc_value, exc_traceback = exc_info
                        if exc_type and exc_value:
                            exception_data = {
                                "type": exc_type.__name__,
                                "message": str(exc_value),
                            }
                except Exception:
                    exception_data = {"error": "Failed to process exception info"}
            return LogRecord(
                timestamp=now,
                level=level.name,
                logger_name=self.name,
                message=str(message),
                data=data,
                caller=caller_info,
                exception=exception_data,
            )
        except Exception:
            return LogRecord(
                timestamp=time.time(),
                level=getattr(level, "name", "INFO"),
                logger_name=self.name,
                message=str(message) if message else "Error creating log record",
                data={},
                caller={},
                exception=None,
            )

    def _emit_simple(self, record: LogRecord) -> None:
        """Simple emit for basic functionality."""
        try:
            try:
                dt = datetime.fromtimestamp(record.timestamp)
                timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                timestamp_str = str(record.timestamp)
            parts = [
                timestamp_str,
                f"[{record.level:>8}]",
                record.logger_name,
                record.message,
            ]
            if record.data:
                try:
                    data_parts = []
                    for key, value in record.data.items():
                        if key != "timestamp_iso":
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
                record_message = getattr(record, "message", "error")
                fallback_msg = "LOG: " + str(record_message)
                print(fallback_msg)
            except Exception:
                pass

    def _log(
        self,
        level: LogLevel,
        message: str,
        exc_info: Optional[Union[bool, tuple, BaseException]] = None,
        **kwargs: Any,
    ) -> Optional[Awaitable[None]]:
        """Internal logging method."""
        try:
            if not self._should_log(level):
                return None
            record = self._create_record(level, message, kwargs, exc_info)
            for filter_obj in self._filters:
                try:
                    if not filter_obj.should_sample(record):
                        return None
                except Exception:
                    pass
            if self._handlers:
                for handler in self._handlers:
                    try:
                        handler.handle(record)
                    except Exception:
                        pass
            else:
                self._emit_simple(record)
        except Exception:
            pass
        return None

    def debug(
        self,
        message: str,
        exc_info: Optional[Union[bool, tuple, BaseException]] = None,
        **kwargs: Any,
    ) -> Optional[Awaitable[None]]:
        """Log a DEBUG level message."""
        try:
            return self._log(LogLevel.DEBUG, message, exc_info, **kwargs)
        except Exception:
            return None

    def info(
        self,
        message: str,
        exc_info: Optional[Union[bool, tuple, BaseException]] = None,
        **kwargs: Any,
    ) -> Optional[Awaitable[None]]:
        """Log an INFO level message."""
        try:
            return self._log(LogLevel.INFO, message, exc_info, **kwargs)
        except Exception:
            return None

    def warning(
        self,
        message: str,
        exc_info: Optional[Union[bool, tuple, BaseException]] = None,
        **kwargs: Any,
    ) -> Optional[Awaitable[None]]:
        """Log a WARNING level message."""
        try:
            return self._log(LogLevel.WARNING, message, exc_info, **kwargs)
        except Exception:
            return None

    def error(
        self,
        message: str,
        exc_info: Optional[Union[bool, tuple, BaseException]] = None,
        **kwargs: Any,
    ) -> Optional[Awaitable[None]]:
        """Log an ERROR level message."""
        try:
            return self._log(LogLevel.ERROR, message, exc_info, **kwargs)
        except Exception:
            return None

    def critical(
        self,
        message: str,
        exc_info: Optional[Union[bool, tuple, BaseException]] = None,
        **kwargs: Any,
    ) -> Optional[Awaitable[None]]:
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
