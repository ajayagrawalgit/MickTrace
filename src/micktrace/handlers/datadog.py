"""Datadog Logs handler for MickTrace.

This handler is lightweight and suitable as a built-in integration example.
It posts single log events to Datadog's Logs Intake API. For production use
consider batching, retries, and the official Datadog client.
"""

import os
import json
from typing import Any, Dict, Optional

from ..types import LogRecord
from .handlers import Handler

try:
    import requests
except Exception:  # pragma: no cover - requests may not be installed for all extras
    requests = None


class DatadogHandler(Handler):
    """Send logs to Datadog Logs Intake API (HTTP).

    Requires either the `datadog` or `requests` package available when used.
    """

    def __init__(self, api_key: Optional[str] = None, dd_site: str = "datadoghq.com", level: str = "INFO") -> None:
        super().__init__(level)
        self.api_key = api_key or os.getenv("DATADOG_API_KEY")
        if not self.api_key:
            raise RuntimeError("DATADOG_API_KEY not provided")
        self.dd_site = dd_site
        self.url = f"https://http-intake.logs.{self.dd_site}/v1/input/{self.api_key}"

    def emit(self, record: LogRecord) -> None:
        if requests is None:
            # If requests is not available we can't send; raise for visibility
            raise RuntimeError(
                "`requests` is required for DatadogHandler but is not installed")

        payload = self._format_record(record)
        headers = {"Content-Type": "application/json"}
        try:
            resp = requests.post(self.url, data=json.dumps(
                payload), headers=headers, timeout=(2.0, 6.0))
            if resp.status_code >= 400:
                # In library code we avoid noisy prints, but surface a RuntimeError so callers can handle it
                raise RuntimeError(
                    f"Datadog returned {resp.status_code}: {resp.text}")
        except Exception:
            # Do not let exceptions escape handler in production; swallow to avoid crashing app
            # Here we swallow but a real implementation should include retries and error logging
            return

    def _format_record(self, record: LogRecord) -> Dict[str, Any]:
        return {
            "timestamp": int(record.timestamp * 1000),
            "message": record.message,
            "service": record.logger_name,
            "status": record.level.lower(),
            "ddsource": "micktrace",
            "logger.name": record.logger_name,
            "attributes": record.data or {},
        }
