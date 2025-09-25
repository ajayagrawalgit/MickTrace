"""
Base Formatter Classes

Defines the interface for all micktrace formatters with support for
structured logging, templating, and performance optimization.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..core.record import LogRecord


class Formatter(ABC):
    """Base class for all micktrace formatters."""

    def __init__(self, **kwargs: Any) -> None:
        self.config = kwargs

    @abstractmethod
    def format(self, record: LogRecord) -> str:
        """Format a log record into a string."""
        pass


class JSONFormatter(Formatter):
    """Format records as JSON."""

    def __init__(self, indent: Optional[int] = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.indent = indent

    def format(self, record: LogRecord) -> str:
        """Format record as JSON."""
        return record.to_json(indent=self.indent)


class LogfmtFormatter(Formatter):
    """Format records as logfmt."""

    def format(self, record: LogRecord) -> str:
        """Format record as logfmt."""
        return record.to_logfmt()


class StructuredFormatter(Formatter):
    """Default structured formatter with human-readable output."""

    def format(self, record: LogRecord) -> str:
        """Format record with structured data."""
        from datetime import datetime

        # Format timestamp
        dt = datetime.fromtimestamp(record.timestamp)
        timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Build message parts
        parts = [
            timestamp_str,
            f"[{record.level:>8}]",
            record.logger_name,
            record.message
        ]

        # Add structured data
        if record.data:
            data_parts = []
            for key, value in record.data.items():
                if key != 'timestamp_iso':
                    data_parts.append(f"{key}={value}")

            if data_parts:
                parts.append(" ".join(data_parts))

        return " ".join(parts)


class SimpleFormatter(Formatter):
    """Simple formatter for basic logging."""

    def format(self, record: LogRecord) -> str:
        """Format record simply."""
        from datetime import datetime

        dt = datetime.fromtimestamp(record.timestamp)
        timestamp_str = dt.strftime("%H:%M:%S")

        return f"{timestamp_str} {record.level} {record.logger_name} {record.message}"
