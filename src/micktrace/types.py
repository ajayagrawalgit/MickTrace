"""
Core types and constants for micktrace.
This module defines fundamental types with zero dependencies to avoid circular imports.
"""

import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple
import datetime
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

try:
    import orjson

    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False


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
        level_upper = level.upper()
        if level_upper in cls.__members__:
            return cls[level_upper]
        raise ValueError(f"Invalid log level: {level}")

    def __lt__(self, other: "LogLevel") -> bool:
        if not isinstance(other, LogLevel):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: "LogLevel") -> bool:
        if not isinstance(other, LogLevel):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: "LogLevel") -> bool:
        if not isinstance(other, LogLevel):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: "LogLevel") -> bool:
        if not isinstance(other, LogLevel):
            return NotImplemented
        return self.value >= other.value


@dataclass
class LogRecord:
    """
    Structured log record with comprehensive metadata.

    This is the core data structure for all log entries.
    Designed for performance, serialization, and type safety.
    """

    # Core required fields
    timestamp: float
    level: str
    logger_name: str
    message: str

    # Optional structured data
    data: Dict[str, Any] = field(default_factory=dict)

    # Caller information
    caller: Dict[str, Any] = field(default_factory=dict)

    # Exception information
    exception: Optional[Dict[str, Any]] = None

    # Tracing and correlation
    trace_id: Optional[str] = field(default_factory=lambda: str(uuid4()))
    correlation_id: Optional[str] = None
    span_id: Optional[str] = None

    # Process/thread information
    process_id: Optional[int] = field(default_factory=os.getpid)
    thread_id: Optional[int] = field(default_factory=threading.get_ident)

    def __post_init__(self) -> None:
        """Post-initialization processing with error handling."""
        try:
            # Ensure timestamp is float
            if isinstance(self.timestamp, datetime):
                self.timestamp = self.timestamp.timestamp()
            elif not isinstance(self.timestamp, (int, float)):
                self.timestamp = time.time()

            # Ensure message is string
            self.message = str(self.message)

            # Add ISO timestamp for readability
            if "timestamp_iso" not in self.data:
                try:
                    dt = datetime.fromtimestamp(self.timestamp)
                    self.data["timestamp_iso"] = dt.isoformat()
                except (ValueError, OSError):
                    # Handle invalid timestamps gracefully
                    self.data["timestamp_iso"] = datetime.now().isoformat()

        except Exception:
            # Ensure the object is always in a valid state
            if not hasattr(self, "message") or not self.message:
                self.message = "Log message"
            if not hasattr(self, "timestamp") or not self.timestamp:
                self.timestamp = time.time()

    def to_dict(self, include_metadata: bool = True) -> Dict[str, Any]:
        """Convert record to dictionary with error handling."""
        try:
            result = {
                "timestamp": self.timestamp,
                "level": self.level,
                "logger_name": self.logger_name,
                "message": self.message,
                "data": self.data.copy() if self.data else {},
            }

            if include_metadata:
                result.update(
                    {
                        "caller": self.caller.copy() if self.caller else {},
                        "exception": self.exception,
                        "trace_id": self.trace_id,
                        "correlation_id": self.correlation_id,
                        "span_id": self.span_id,
                        "process_id": self.process_id,
                        "thread_id": self.thread_id,
                    }
                )

            return result

        except Exception:
            # Fallback to minimal record
            return {
                "timestamp": getattr(self, "timestamp", time.time()),
                "level": getattr(self, "level", "INFO"),
                "logger_name": getattr(self, "logger_name", "unknown"),
                "message": getattr(self, "message", "Log record error"),
                "data": {},
            }

    def to_json(self, **kwargs: Any) -> str:
        """Convert record to JSON string with error handling."""
        try:
            data = self.to_dict()

            if HAS_ORJSON:
                # Use orjson for better performance
                try:
                    return orjson.dumps(data, **kwargs).decode("utf-8")
                except Exception:
                    # Fallback if orjson fails
                    pass

            # Standard library json fallback
            import json

            return json.dumps(data, default=str, **kwargs)

        except Exception:
            # Ultimate fallback - FIXED: removed malformed f-string
            level = getattr(self, "level", "INFO")
            message = getattr(self, "message", "error")
            timestamp = getattr(self, "timestamp", time.time())
            return (
                '{"level": "'
                + level
                + '", "message": "'
                + message
                + '", "timestamp": '
                + str(timestamp)
                + "}"
            )

    def to_logfmt(self) -> str:
        """Convert record to logfmt format with error handling."""
        try:
            parts = [
                f"timestamp={self.timestamp}",
                f"level={self.level}",
                f"logger={self._quote_value(self.logger_name)}",
                f"message={self._quote_value(self.message)}",
            ]

            # Add structured data
            if self.data:
                for key, value in self.data.items():
                    if key != "timestamp_iso":
                        try:
                            parts.append(f"{key}={self._quote_value(value)}")
                        except Exception:
                            parts.append(f"{key}=<error>")

            # Add trace information if present
            if self.trace_id:
                parts.append(f"trace_id={self.trace_id}")
            if self.correlation_id:
                parts.append(f"correlation_id={self.correlation_id}")

            return " ".join(parts)

        except Exception:
            # Minimal fallback
            return f"level={self.level} message={self.message}"

    def _quote_value(self, value: Any) -> str:
        """Quote a value for logfmt output with error handling."""
        try:
            str_value = str(value)
            if " " in str_value or '"' in str_value or "=" in str_value:
                # Escape quotes and wrap in quotes
                escaped = str_value.replace('"', '"')
                return f'"{escaped}"'
            return str_value
        except Exception:
            return '"<error>"'

    def __str__(self) -> str:
        """String representation for debugging."""
        try:
            return f"LogRecord({self.level}, {self.logger_name}, {self.message})"
        except Exception:
            return "LogRecord(<error>)"

    def __repr__(self) -> str:
        """Detailed representation with error handling."""
        try:
            return (
                f"LogRecord(timestamp={self.timestamp}, level='{self.level}', "
                f"logger_name='{self.logger_name}', message='{self.message}', "
                f"data_keys={list(self.data.keys()) if self.data else []}, "
                f"trace_id='{self.trace_id}')"
            )
        except Exception:
            return "LogRecord(<repr error>)"
