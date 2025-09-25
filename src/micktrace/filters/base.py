"""
Base Filter Classes

Defines filtering interfaces for log records with support for
level, logger name, content, and custom filtering.
"""

import re
from abc import ABC, abstractmethod
from typing import Any, Pattern, List, Callable

from ..core.record import LogRecord


class Filter(ABC):
    """Base class for all micktrace filters."""

    @abstractmethod
    def filter(self, record: LogRecord) -> bool:
        """Return True if record should be logged, False otherwise."""
        pass


class LevelFilter(Filter):
    """Filter by log level."""

    def __init__(self, min_level: str, max_level: str = "CRITICAL") -> None:
        from ..core.logger import LogLevel
        self.min_level = LogLevel.from_string(min_level)
        self.max_level = LogLevel.from_string(max_level)

    def filter(self, record: LogRecord) -> bool:
        from ..core.logger import LogLevel
        level = LogLevel.from_string(record.level)
        return self.min_level <= level <= self.max_level


class LoggerFilter(Filter):
    """Filter by logger name pattern."""

    def __init__(self, pattern: str, exclude: bool = False) -> None:
        self.pattern = re.compile(pattern)
        self.exclude = exclude

    def filter(self, record: LogRecord) -> bool:
        matches = bool(self.pattern.search(record.logger_name))
        return not matches if self.exclude else matches


class ContentFilter(Filter):
    """Filter by message content."""

    def __init__(self, pattern: str, exclude: bool = False) -> None:
        self.pattern = re.compile(pattern)
        self.exclude = exclude

    def filter(self, record: LogRecord) -> bool:
        matches = bool(self.pattern.search(record.message))
        return not matches if self.exclude else matches


class CallableFilter(Filter):
    """Filter using a callable function."""

    def __init__(self, func: Callable[[LogRecord], bool]) -> None:
        self.func = func

    def filter(self, record: LogRecord) -> bool:
        return self.func(record)
