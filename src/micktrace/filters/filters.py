"""
Filters for micktrace with comprehensive error handling.
"""

from typing import Any, Callable

from ..types import LogRecord, LogLevel


class Filter:
    """Base filter class."""

    def __init__(self, **kwargs: Any) -> None:
        self.config = kwargs or {}

    def filter(self, record: LogRecord) -> bool:
        """Return True if record should be logged, False otherwise."""
        try:
            return True
        except Exception:
            return True


class LevelFilter(Filter):
    """Filter by log level."""

    def __init__(self, min_level: str = "DEBUG", max_level: str = "CRITICAL", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        try:
            self.min_level = LogLevel.from_string(min_level)
            self.max_level = LogLevel.from_string(max_level)
        except Exception:
            self.min_level = LogLevel.DEBUG
            self.max_level = LogLevel.CRITICAL

    def filter(self, record: LogRecord) -> bool:
        """Filter by log level."""
        try:
            level = LogLevel.from_string(record.level)
            return self.min_level <= level <= self.max_level
        except Exception:
            return True


class CallableFilter(Filter):
    """Filter using a callable function."""

    def __init__(self, func: Callable[[LogRecord], bool], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.func = func if callable(func) else lambda r: True

    def filter(self, record: LogRecord) -> bool:
        """Filter using callable function."""
        try:
            return bool(self.func(record))
        except Exception:
            return True
