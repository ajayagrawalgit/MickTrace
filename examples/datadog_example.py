"""
Datadog integration example for MickTrace

This script demonstrates a minimal Datadog Logs integration using the Datadog HTTP Logs Intake API.
It creates a simple `DatadogHTTPHandler` compatible with MickTrace's handler interface and sends a few
structured logs to Datadog. For real production use prefer the official Datadog library (datadog-api-client)
or a more robust batching/async implementation.

Setup:
    1. Install requests: pip install requests
    2. Set environment variable DATADOG_API_KEY with your Datadog Logs API key.
    3. Run: python examples/datadog_example.py

Note: This example sends logs directly to Datadog over the network. Use with caution and avoid spamming
your Datadog account during testing.
"""

import os
import json
import time
from typing import Any, Dict

import requests

import micktrace
from micktrace.core.logger import Logger
from micktrace.handlers.handlers import Handler
from micktrace.types import LogRecord, LogLevel


class DatadogHTTPHandler(Handler):
    """Minimal Datadog Logs HTTP handler.

    This handler posts log events to Datadog's Logs Intake API v1.
    It expects an API key in the DATADOG_API_KEY environment variable.
    """

    def __init__(self, api_key: str = None, dd_site: str = "datadoghq.com", level: str = "INFO") -> None:
        super().__init__(level)
        self.api_key = api_key or os.getenv("DATADOG_API_KEY")
        if not self.api_key:
            raise RuntimeError("DATADOG_API_KEY not provided in environment")
        self.url = f"https://http-intake.logs.{dd_site}/v1/input/{self.api_key}"
        # Small connection timeout to avoid hanging example
        self.timeout = (2.0, 5.0)

    def emit(self, record: LogRecord) -> None:
        try:
            payload = self._format_record(record)
            headers = {"Content-Type": "application/json"}
            resp = requests.post(self.url, data=json.dumps(
                payload), headers=headers, timeout=self.timeout)
            if resp.status_code >= 400:
                # For demo purposes just print error
                print(f"Datadog HTTP error: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Failed to send log to Datadog: {e}")

    def _format_record(self, record: LogRecord) -> Dict[str, Any]:
        # Datadog expects one event per line for their Logs Intake, but sending JSON array is accepted too.
        # Keep it simple: send a single JSON object representing the log event.
        ev = {
            "timestamp": int(record.timestamp * 1000),  # milliseconds
            "message": record.message,
            "service": record.logger_name,
            "status": record.level.lower(),
            "ddsource": "micktrace",
            "logger.name": record.logger_name,
            "attributes": record.data or {}
        }
        return ev


def main() -> None:
    # Short check for API key
    dd_api_key = os.getenv("DATADOG_API_KEY")
    if not dd_api_key:
        print("DATADOG_API_KEY environment variable is not set. Skipping real send.\n")
    # Configure micktrace to use our DatadogHTTPHandler for this example
    micktrace.configure(enabled=True, level="INFO",
                        handlers=[{"type": "null"}])
    # Create a logger and attach the Datadog handler directly
    logger = micktrace.get_logger("datadog-demo")
    # Clear any existing handlers and add our Datadog handler
    logger.clear_handlers()
    try:
        dd_handler = DatadogHTTPHandler(api_key=dd_api_key)
        logger.add_handler(dd_handler)
    except RuntimeError:
        # If no API key, use a memory handler to demonstrate
        from micktrace.handlers.console import MemoryHandler
        mem = MemoryHandler()
        logger.add_handler(mem)
        print("No DATADOG_API_KEY found - logs will be kept in memory for demo.")
    # Send some structured logs
    logger.info("Datadog integration demo - startup",
                environment="demo", version="1.0")
    for i in range(3):
        logger.info("processing.event", event_id=i,
                    user=f"user-{i}", latency_ms=5 * i)
        time.sleep(0.2)
    logger.warning("Datadog integration demo - finishing", processed=3)
    print("Demo finished.")


if __name__ == "__main__":
    main()
