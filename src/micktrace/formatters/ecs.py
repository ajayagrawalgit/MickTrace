"""Elastic Common Schema (ECS) formatter for MickTrace."""

import json
from datetime import datetime
from typing import Any, Dict

from ..types import LogRecord


class ECSFormatter:
    """Formats logs according to Elastic Common Schema (ECS).

    References:
        - https://www.elastic.co/guide/en/ecs/current/index.html
    """

    LOG_LEVEL_SEVERITY_MAP = {
        "DEBUG": 7,
        "INFO": 6,
        "WARNING": 4,
        "ERROR": 3,
        "CRITICAL": 2,
    }

    def __init__(
        self,
        version: str = "1.12.1",
        dataset: str = "micktrace",
        include_source_code: bool = True,
    ):
        """Initialize the formatter.

        Args:
            version: ECS version to use
            dataset: Dataset name for the logs
            include_source_code: Whether to include source code information
        """
        self.version = version
        self.dataset = dataset
        self.include_source_code = include_source_code

    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp as ISO 8601 format."""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.isoformat() + "Z"
        except Exception:
            return datetime.utcnow().isoformat() + "Z"

    def _extract_http_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract HTTP-related fields according to ECS."""
        http = {}

        field_mappings = {
            "http_method": "method",
            "http_url": "url",
            "http_version": "version",
            "http_status_code": "response.status_code",
            "http_request_id": "request.id",
            "http_referrer": "request.referrer",
            "http_user_agent": "request.user_agent",
            "http_request_bytes": "request.bytes",
            "http_response_bytes": "response.bytes",
        }

        for src, dest in field_mappings.items():
            if src in data:
                parts = dest.split(".")
                current = http
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = data[src]

        return http if http else None

    def _extract_url_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract URL-related fields according to ECS."""
        url = {}

        field_mappings = {
            "url_original": "original",
            "url_domain": "domain",
            "url_path": "path",
            "url_query": "query",
            "url_fragment": "fragment",
            "url_port": "port",
            "url_scheme": "scheme",
        }

        for src, dest in field_mappings.items():
            if src in data:
                url[dest] = data[src]

        return url if url else None

    def _extract_user_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user-related fields according to ECS."""
        user = {}

        field_mappings = {
            "user_id": "id",
            "user_name": "name",
            "user_email": "email",
            "user_domain": "domain",
            "user_roles": "roles",
        }

        for src, dest in field_mappings.items():
            if src in data:
                user[dest] = data[src]

        return user if user else None

    def _extract_error_fields(self, exception: Dict[str, Any]) -> Dict[str, Any]:
        """Extract error-related fields according to ECS."""
        return {
            "type": exception.get("type", "Unknown"),
            "message": exception.get("message", ""),
            "stack_trace": exception.get("stacktrace", ""),
        }

    def _extract_trace_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract distributed tracing fields according to ECS."""
        trace = {}

        field_mappings = {
            "trace_id": "id",
            "span_id": "span.id",
            "parent_span_id": "parent.id",
            "trace_sampled": "sampled",
        }

        for src, dest in field_mappings.items():
            if src in data:
                parts = dest.split(".")
                current = trace
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = data[src]

        return trace if trace else None

    def format(self, record: LogRecord) -> str:
        """Format a log record according to ECS specification."""
        try:
            # Create base document
            doc = {
                "@timestamp": self._format_timestamp(record.timestamp),
                "ecs": {"version": self.version},
                "log": {
                    "level": record.level,
                    "logger": record.logger_name,
                    "origin": (
                        {
                            "file": {
                                "name": record.caller.get("filename"),
                                "line": record.caller.get("lineno"),
                            },
                            "function": record.caller.get("function"),
                        }
                        if self.include_source_code and record.caller
                        else None
                    ),
                },
                "message": record.message,
                "labels": {"dataset": self.dataset},
            }

            # Add data fields
            if record.data:
                # Extract ECS-specific fields
                http_fields = self._extract_http_fields(record.data)
                if http_fields:
                    doc["http"] = http_fields

                url_fields = self._extract_url_fields(record.data)
                if url_fields:
                    doc["url"] = url_fields

                user_fields = self._extract_user_fields(record.data)
                if user_fields:
                    doc["user"] = user_fields

                trace_fields = self._extract_trace_fields(record.data)
                if trace_fields:
                    doc["trace"] = trace_fields

                # Add remaining fields as custom fields
                custom_fields = {}
                for key, value in record.data.items():
                    if not any(
                        key.startswith(prefix)
                        for prefix in ["http_", "url_", "user_", "trace_"]
                    ):
                        custom_fields[key] = value

                if custom_fields:
                    doc["micktrace"] = custom_fields

            # Add exception information
            if record.exception:
                doc["error"] = self._extract_error_fields(record.exception)

            return json.dumps(doc)

        except Exception as e:
            # Fallback format if anything goes wrong
            return json.dumps(
                {
                    "@timestamp": datetime.utcnow().isoformat() + "Z",
                    "ecs": {"version": self.version},
                    "log": {"level": "ERROR", "logger": "ECSFormatter"},
                    "message": f"Error formatting log: {str(e)}",
                    "error": {"message": str(e), "type": type(e).__name__},
                    "labels": {"dataset": self.dataset},
                }
            )
