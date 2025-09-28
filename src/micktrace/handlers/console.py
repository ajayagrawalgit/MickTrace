"""Console handler for micktrace."""

import sys
from typing import Any, TextIO, Optional

from ..types import LogRecord


class ConsoleHandler:
    def __init__(self, name: str = "console", **kwargs: Any) -> None:
        self.name = name
        self.stream = sys.stderr
        self.config = kwargs

    def emit(self, record: LogRecord) -> None:
        try:
            print(f"\nDEBUG ConsoleHandler: record level={record.level} message={record.message}")
            print(f"DEBUG ConsoleHandler: my level={getattr(self, 'level', 'NOTSET')}")
            
            message = str(record.timestamp) + " " + record.level + " " + record.message
            self.stream.write(message + "\n")
            self.stream.flush()
        except Exception as e:
            print(f"Failed to emit to console: {e}")


class NullHandler:
    def __init__(self, name: str = "null", **kwargs: Any) -> None:
        self.name = name
        self.config = kwargs

    def emit(self, record: LogRecord) -> None:
        pass


class MemoryHandler:
    def __init__(self, name: str = "memory", **kwargs: Any) -> None:
        self.name = name
        self.records = []
        self.config = kwargs

    def emit(self, record: LogRecord) -> None:
        try:
            self.records.append(record)
        except Exception:
            pass

    def clear(self) -> None:
        self.records = []

    def get_records(self):
        return self.records
