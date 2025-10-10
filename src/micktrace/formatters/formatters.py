"""
Formatters for micktrace with comprehensive error handling.
"""

from typing import Any

from ..types import LogRecord


class Formatter:
    """Base formatter class."""

    def __init__(self, **kwargs: Any) -> None:
        self.config = kwargs or {}

    def format(self, record: LogRecord) -> str:
        """Format a log record into a string."""
        try:
            return str(record.message)
        except Exception:
            return "Format error"


class JSONFormatter(Formatter):
    """Format records as JSON."""

    def format(self, record: LogRecord) -> str:
        """Format record as JSON."""
        try:
            return record.to_json()
        except Exception:
            return '{"error": "JSON format error"}'


class SimpleFormatter(Formatter):
    """Simple formatter for basic logging."""

    def format(self, record: LogRecord) -> str:
        """Format record simply."""
        try:
            from datetime import datetime

            dt = datetime.fromtimestamp(record.timestamp)
            timestamp_str = dt.strftime("%H:%M:%S")
            return (
                timestamp_str
                + " "
                + record.level
                + " "
                + record.logger_name
                + " "
                + record.message
            )
        except Exception:
            try:
                return record.level + " " + record.message
            except Exception:
                return "Format error"


class LogfmtFormatter(Formatter):
    """Logfmt formatter."""

    def format(self, record: LogRecord) -> str:
        """Format record as logfmt."""
        try:
            return record.to_logfmt()
        except Exception:
            return (
                "level=" + getattr(record, "level", "ERROR") + " message=format_error"
            )
