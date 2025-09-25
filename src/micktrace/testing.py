"""
Testing utilities for micktrace.

Provides tools for capturing and verifying log output in tests.
"""

import threading
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Iterator

from .core.record import LogRecord
from .handlers.base import MemoryHandler
from .core.logger import Logger


class LogCapture:
    """Capture log records for testing."""

    def __init__(self, logger_name: Optional[str] = None, level: str = "DEBUG") -> None:
        self.logger_name = logger_name
        self.level = level
        self.records: List[LogRecord] = []
        self.handler: Optional[MemoryHandler] = None
        self.original_handlers: List[Any] = []
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start capturing logs."""
        with self._lock:
            if self.handler is not None:
                return

            self.handler = MemoryHandler(name="test_capture", level=self.level)

            # Replace handlers on target logger
            if self.logger_name:
                logger = Logger.get(self.logger_name)
                # Store original handlers
                self.original_handlers = logger._handler_manager.get_all_handlers()
                # Replace with capture handler
                for handler in self.original_handlers:
                    logger._handler_manager.remove_handler(handler.name)
                logger._handler_manager.add_handler(self.handler)
            else:
                # Capture all logs by adding to root configuration
                from .config.configuration import get_configuration, set_configuration
                config = get_configuration()
                new_handlers = config.handlers + [
                    type('HandlerConfig', (), {
                        'type': 'memory',
                        'level': self.level,
                        'format': 'structured',
                        'enabled': True,
                        'config': {'name': 'test_capture'}
                    })()
                ]
                config.handlers = new_handlers
                set_configuration(config)

    def stop(self) -> None:
        """Stop capturing logs."""
        with self._lock:
            if self.handler is None:
                return

            # Get captured records
            self.records = self.handler.get_records()

            # Restore original handlers
            if self.logger_name and self.original_handlers:
                logger = Logger.get(self.logger_name)
                logger._handler_manager.remove_handler(self.handler.name)
                for handler in self.original_handlers:
                    logger._handler_manager.add_handler(handler)

            self.handler = None

    def clear(self) -> None:
        """Clear captured records."""
        with self._lock:
            self.records.clear()
            if self.handler:
                self.handler.clear()

    def get_records(self, level: Optional[str] = None) -> List[LogRecord]:
        """Get captured records, optionally filtered by level."""
        with self._lock:
            if level is None:
                return self.records.copy()
            else:
                return [r for r in self.records if r.level == level]

    def assert_logged(
        self,
        level: str,
        message: Optional[str] = None,
        logger_name: Optional[str] = None,
        **data: Any
    ) -> bool:
        """Assert that a log record was captured."""
        for record in self.get_records(level):
            if logger_name and record.logger_name != logger_name:
                continue

            if message and message not in record.message:
                continue

            # Check data fields
            match = True
            for key, value in data.items():
                if key not in record.data or record.data[key] != value:
                    match = False
                    break

            if match:
                return True

        return False

    def __enter__(self) -> "LogCapture":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()

    def __len__(self) -> int:
        """Return number of captured records."""
        return len(self.records)

    def __getitem__(self, index: int) -> LogRecord:
        """Get record by index."""
        return self.records[index]


@contextmanager
def capture_logs(
    logger_name: Optional[str] = None, 
    level: str = "DEBUG"
) -> Iterator[LogCapture]:
    """Context manager for capturing logs."""
    capture = LogCapture(logger_name, level)
    with capture:
        yield capture


class MockHandler:
    """Mock handler for testing."""

    def __init__(self, name: str = "mock") -> None:
        self.name = name
        self.records: List[LogRecord] = []
        self.formatted_records: List[str] = []
        self.calls: List[Dict[str, Any]] = []

    def should_handle(self, record: LogRecord) -> bool:
        """Always handle records."""
        return True

    def format_record(self, record: LogRecord) -> str:
        """Format record."""
        return f"{record.level} {record.logger_name} {record.message}"

    def handle_sync(self, record: LogRecord) -> None:
        """Handle record synchronously."""
        self.records.append(record)
        self.formatted_records.append(self.format_record(record))
        self.calls.append({"method": "handle_sync", "record": record})

    async def handle_async(self, record: LogRecord) -> None:
        """Handle record asynchronously."""
        self.records.append(record)
        self.formatted_records.append(self.format_record(record))
        self.calls.append({"method": "handle_async", "record": record})

    def clear(self) -> None:
        """Clear all captured data."""
        self.records.clear()
        self.formatted_records.clear()
        self.calls.clear()


def create_test_logger(name: str = "test", level: str = "DEBUG") -> Logger:
    """Create a logger for testing with memory handler."""
    logger = Logger.get(name)
    logger.set_level(level)

    # Add memory handler
    handler = MemoryHandler(name=f"{name}_handler", level=level)
    logger._handler_manager.add_handler(handler)

    return logger


def assert_log_record(
    record: LogRecord,
    level: str,
    message: Optional[str] = None,
    logger_name: Optional[str] = None,
    **data: Any
) -> None:
    """Assert properties of a log record."""
    assert record.level == level, f"Expected level {level}, got {record.level}"

    if message is not None:
        assert message in record.message, f"Message '{message}' not found in '{record.message}'"

    if logger_name is not None:
        assert record.logger_name == logger_name, f"Expected logger {logger_name}, got {record.logger_name}"

    for key, value in data.items():
        assert key in record.data, f"Key '{key}' not found in record data"
        assert record.data[key] == value, f"Expected {key}={value}, got {record.data[key]}"
