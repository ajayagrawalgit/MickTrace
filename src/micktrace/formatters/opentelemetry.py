"""OpenTelemetry formatter for MickTrace with trace correlation support."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
except ImportError:
    trace = None

from ..types import LogRecord

class OpenTelemetryFormatter:
    """Formats logs according to OpenTelemetry semantic conventions."""
    
    SEVERITY_MAP = {
        "DEBUG": "DEBUG",
        "INFO": "INFO",
        "WARNING": "WARN",
        "ERROR": "ERROR",
        "CRITICAL": "FATAL"
    }
    
    def __init__(self):
        """Initialize the formatter."""
        if trace is None:
            raise ImportError(
                "OpenTelemetry is required for OpenTelemetryFormatter. "
                "Install with: pip install opentelemetry-api opentelemetry-sdk"
            )
            
    def _get_trace_context(self) -> Dict[str, str]:
        """Get the current trace context."""
        context = {}
        
        try:
            span = trace.get_current_span()
            if span:
                context.update({
                    "trace_id": format(span.get_span_context().trace_id, "032x"),
                    "span_id": format(span.get_span_context().span_id, "016x")
                })
                
                trace_flags = span.get_span_context().trace_flags
                if trace_flags:
                    context["trace_flags"] = str(trace_flags)
        except Exception:
            pass
            
        return context
        
    def _convert_attributes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert log data to OpenTelemetry attributes.
        
        Follows semantic conventions from:
        https://opentelemetry.io/docs/specs/otel/logs/semantic_conventions/
        """
        attributes = {}
        
        # Convert known fields to standard attributes
        known_mappings = {
            "logger_name": "logger.name",
            "thread_name": "thread.name",
            "thread_id": "thread.id",
            "process_name": "process.name",
            "process_id": "process.id",
            "correlation_id": "log.correlation_id",
            "duration_ms": "duration_ms",
            "http.method": "http.method",
            "http.url": "http.url",
            "http.status_code": "http.status_code",
            "db.system": "db.system",
            "db.name": "db.name",
            "db.operation": "db.operation",
            "service.name": "service.name",
            "service.version": "service.version",
            "service.namespace": "service.namespace"
        }
        
        for key, value in data.items():
            if key in known_mappings:
                attributes[known_mappings[key]] = value
            else:
                # Flatten nested dictionaries
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        flat_key = f"{key}.{sub_key}"
                        attributes[flat_key] = str(sub_value)
                else:
                    attributes[key] = str(value)
                    
        return attributes
        
    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp as ISO 8601 with nanosecond precision."""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.isoformat() + "Z"
        except Exception:
            return datetime.utcnow().isoformat() + "Z"
            
    def _get_severity_number(self, level: str) -> int:
        """Convert log level to OpenTelemetry severity number."""
        severity_map = {
            "TRACE": 1,
            "DEBUG": 5,
            "INFO": 9,
            "WARN": 13,
            "ERROR": 17,
            "FATAL": 21
        }
        return severity_map.get(level.upper(), 9)  # Default to INFO
        
    def format(self, record: LogRecord) -> str:
        """Format a log record according to OpenTelemetry specification."""
        try:
            # Get current trace context
            trace_context = self._get_trace_context()
            
            # Convert record to OTel format
            log_data = {
                "timestamp": self._format_timestamp(record.timestamp),
                "severity_text": self.SEVERITY_MAP.get(record.level, record.level),
                "severity_number": self._get_severity_number(record.level),
                "body": record.message,
                "attributes": self._convert_attributes(record.data or {})
            }
            
            # Add trace context if available
            if trace_context:
                log_data.update(trace_context)
                
            # Add exception data if present
            if record.exception:
                exception_data = record.exception
                log_data["attributes"].update({
                    "exception.type": exception_data.get("type", "Unknown"),
                    "exception.message": exception_data.get("message", ""),
                    "exception.stacktrace": exception_data.get("stacktrace", "")
                })
                
            # Add source code information
            if record.caller:
                log_data["attributes"].update({
                    "code.function": record.caller.get("function", ""),
                    "code.filepath": record.caller.get("filename", ""),
                    "code.lineno": record.caller.get("lineno", 0)
                })
                
            return json.dumps(log_data)
            
        except Exception as e:
            # Fallback format if anything goes wrong
            return json.dumps({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "severity_text": "ERROR",
                "severity_number": 17,
                "body": f"Error formatting log: {str(e)}",
                "attributes": {
                    "original_message": record.message,
                    "formatter_error": str(e)
                }
            })