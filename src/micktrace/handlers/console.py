"""Console handler for micktrace."""

import sys
from typing import Any, TextIO, Optional

from ..types import LogRecord


class ConsoleHandler:
    def __init__(self, name: str = "console", level: str = "INFO", **kwargs: Any) -> None:
        self.name = name
        self.level = level
        self.stream = sys.stderr
        self.config = kwargs

    def handle(self, record: LogRecord) -> None:
        """Handle a log record."""
        try:
            # Check level if specified
            if hasattr(self, 'level'):
                from ..types import LogLevel
                record_level = LogLevel.from_string(record.level)
                handler_level = LogLevel.from_string(self.level)
                if record_level < handler_level:
                    return
                    
            self.emit(record)
        except Exception:
            pass

    def emit(self, record: LogRecord) -> None:
        try:
            message = str(record.timestamp) + " " + record.level + " " + record.message
            self.stream.write(message + "\n")
            self.stream.flush()
        except Exception:
            pass


class NullHandler:
    def __init__(self, name: str = "null", level: str = "INFO", **kwargs: Any) -> None:
        self.name = name
        self.level = level
        self.config = kwargs

    def handle(self, record: LogRecord) -> None:
        """Handle a log record - NullHandler does nothing."""
        pass

    def emit(self, record: LogRecord) -> None:
        pass


class MemoryHandler:
    def __init__(self, name: str = "memory", level: str = "INFO", **kwargs: Any) -> None:
        self.name = name
        self.level = level
        self.records = []
        self.config = kwargs

    def handle(self, record: LogRecord) -> None:
        """Handle a log record."""
        try:
            # Check level if specified
            if hasattr(self, 'level'):
                from ..types import LogLevel
                record_level = LogLevel.from_string(record.level)
                handler_level = LogLevel.from_string(self.level)
                if record_level < handler_level:
                    return
                    
            self.emit(record)
        except Exception:
            pass

    def emit(self, record: LogRecord) -> None:
        try:
            self.records.append(record)
        except Exception:
            pass

    def clear(self) -> None:
        self.records = []

    def get_records(self):
        return self.records
