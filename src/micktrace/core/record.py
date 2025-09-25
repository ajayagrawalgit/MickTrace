"""
Log Record Implementation

LogRecord represents a single log entry with all associated metadata.
Designed for structured logging with type safety and serialization support.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, Optional, List
from uuid import uuid4

try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False


@dataclass
class LogRecord:
    """
    Structured log record with comprehensive metadata.

    All log data is structured by default with automatic serialization
    support and type safety.
    """

    # Core fields
    timestamp: float
    level: str
    logger_name: str
    message: str

    # Structured data
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
    process_id: Optional[int] = field(default_factory=lambda: __import__('os').getpid())
    thread_id: Optional[int] = field(default_factory=lambda: __import__('threading').get_ident())

    # Performance timing
    duration: Optional[float] = None

    def __post_init__(self) -> None:
        """Post-initialization processing."""
        # Ensure timestamp is float
        if isinstance(self.timestamp, datetime):
            self.timestamp = self.timestamp.timestamp()

        # Add ISO timestamp for readability
        self.data['timestamp_iso'] = datetime.fromtimestamp(
            self.timestamp
        ).isoformat()

    def to_dict(self, include_metadata: bool = True) -> Dict[str, Any]:
        """Convert record to dictionary."""
        result = asdict(self)

        if not include_metadata:
            # Remove internal fields
            for key in ['process_id', 'thread_id', 'caller']:
                result.pop(key, None)

        return result

    def to_json(self, **kwargs: Any) -> str:
        """Convert record to JSON string."""
        data = self.to_dict()

        if HAS_ORJSON:
            # Use orjson for better performance
            return orjson.dumps(data, **kwargs).decode('utf-8')
        else:
            # Fallback to standard json
            return json.dumps(data, default=str, **kwargs)

    def to_logfmt(self) -> str:
        """Convert record to logfmt format."""
        parts = []

        # Core fields first
        parts.extend([
            f"timestamp={self.timestamp}",
            f"level={self.level}",
            f"logger={self.logger_name}",
            f"message={self._quote_value(self.message)}"
        ])

        # Add structured data
        for key, value in self.data.items():
            if key != 'timestamp_iso':  # Skip auto-added ISO timestamp
                parts.append(f"{key}={self._quote_value(value)}")

        # Add trace information if present
        if self.trace_id:
            parts.append(f"trace_id={self.trace_id}")
        if self.correlation_id:
            parts.append(f"correlation_id={self.correlation_id}")

        # Add caller info
        if self.caller:
            parts.append(f"module={self.caller.get('module', 'unknown')}")
            parts.append(f"function={self.caller.get('function', 'unknown')}")
            parts.append(f"line={self.caller.get('lineno', 0)}")

        return ' '.join(parts)

    def _quote_value(self, value: Any) -> str:
        """Quote a value for logfmt output."""
        str_value = str(value)
        if ' ' in str_value or '"' in str_value or '=' in str_value:
            # Escape quotes and wrap in quotes
            escaped = str_value.replace('"', '\"')
            return f'"{escaped}"'
        return str_value

    def add_context(self, **kwargs: Any) -> None:
        """Add additional context to the record."""
        self.data.update(kwargs)

    def with_duration(self, duration: float) -> "LogRecord":
        """Return a copy with duration set."""
        new_record = LogRecord(
            timestamp=self.timestamp,
            level=self.level,
            logger_name=self.logger_name,
            message=self.message,
            data=self.data.copy(),
            caller=self.caller.copy(),
            exception=self.exception,
            trace_id=self.trace_id,
            correlation_id=self.correlation_id,
            span_id=self.span_id,
            process_id=self.process_id,
            thread_id=self.thread_id,
            duration=duration
        )
        return new_record

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"LogRecord({self.level}, {self.logger_name}, {self.message})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"LogRecord(timestamp={self.timestamp}, level='{self.level}', "
            f"logger_name='{self.logger_name}', message='{self.message}', "
            f"data_keys={list(self.data.keys())}, trace_id='{self.trace_id}')"
        )


class RecordBuilder:
    """Builder for creating log records with fluent interface."""

    def __init__(self) -> None:
        self._timestamp = time.time()
        self._level = "INFO"
        self._logger_name = "root"
        self._message = ""
        self._data: Dict[str, Any] = {}
        self._caller: Dict[str, Any] = {}
        self._exception: Optional[Dict[str, Any]] = None
        self._trace_id: Optional[str] = None
        self._correlation_id: Optional[str] = None
        self._duration: Optional[float] = None

    def timestamp(self, timestamp: float) -> "RecordBuilder":
        self._timestamp = timestamp
        return self

    def level(self, level: str) -> "RecordBuilder":
        self._level = level
        return self

    def logger_name(self, name: str) -> "RecordBuilder":
        self._logger_name = name
        return self

    def message(self, message: str) -> "RecordBuilder":
        self._message = message
        return self

    def data(self, **kwargs: Any) -> "RecordBuilder":
        self._data.update(kwargs)
        return self

    def caller(self, **kwargs: Any) -> "RecordBuilder":
        self._caller.update(kwargs)
        return self

    def exception(self, exc_info: Dict[str, Any]) -> "RecordBuilder":
        self._exception = exc_info
        return self

    def trace_id(self, trace_id: str) -> "RecordBuilder":
        self._trace_id = trace_id
        return self

    def correlation_id(self, correlation_id: str) -> "RecordBuilder":
        self._correlation_id = correlation_id
        return self

    def duration(self, duration: float) -> "RecordBuilder":
        self._duration = duration
        return self

    def build(self) -> LogRecord:
        """Build the log record."""
        return LogRecord(
            timestamp=self._timestamp,
            level=self._level,
            logger_name=self._logger_name,
            message=self._message,
            data=self._data,
            caller=self._caller,
            exception=self._exception,
            trace_id=self._trace_id,
            correlation_id=self._correlation_id,
            duration=self._duration
        )
