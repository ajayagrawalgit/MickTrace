"""
Tests for core logger functionality.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import micktrace
from micktrace.core.logger import Logger, LogLevel
from micktrace.core.record import LogRecord
from micktrace.testing import capture_logs, LogCapture


class TestLogger:
    """Test Logger class."""

    def test_logger_creation(self):
        """Test basic logger creation."""
        logger = micktrace.get_logger("test")
        assert isinstance(logger, Logger)
        assert logger.name == "test"

    def test_log_levels(self):
        """Test logging at different levels."""
        with capture_logs() as capture:
            micktrace.configure(level="DEBUG", handlers=["memory"])
            logger = micktrace.get_logger("test.levels")

            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")

            records = capture.get_records()
            assert len(records) == 5

            levels = [r.level for r in records]
            assert levels == ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_structured_logging(self):
        """Test structured logging with additional data."""
        with capture_logs() as capture:
            micktrace.configure(level="INFO", handlers=["memory"])
            logger = micktrace.get_logger("test.structured")

            logger.info("User login", user_id=123, action="login", success=True)

            records = capture.get_records()
            assert len(records) == 1

            record = records[0]
            assert record.message == "User login"
            assert record.data["user_id"] == 123
            assert record.data["action"] == "login"
            assert record.data["success"] is True

    def test_level_filtering(self):
        """Test that log levels are filtered correctly."""
        with capture_logs() as capture:
            micktrace.configure(level="WARNING", handlers=["memory"])
            logger = micktrace.get_logger("test.filtering")

            logger.debug("Should not appear")
            logger.info("Should not appear") 
            logger.warning("Should appear")
            logger.error("Should appear")

            records = capture.get_records()
            assert len(records) == 2
            assert all(r.level in ["WARNING", "ERROR"] for r in records)

    def test_context_propagation(self):
        """Test that context is properly propagated."""
        with capture_logs() as capture:
            micktrace.configure(level="INFO", handlers=["memory"])
            logger = micktrace.get_logger("test.context")

            with micktrace.context(request_id="req_123", user_id=456):
                logger.info("Processing request")

            records = capture.get_records()
            assert len(records) == 1

            record = records[0]
            assert record.data["request_id"] == "req_123"
            assert record.data["user_id"] == 456

    def test_bound_logger(self):
        """Test bound logger functionality."""
        with capture_logs() as capture:
            micktrace.configure(level="INFO", handlers=["memory"])
            logger = micktrace.get_logger("test.bound")

            bound = logger.bind(service="auth", version="1.0")
            bound.info("Service started", port=8080)

            records = capture.get_records()
            assert len(records) == 1

            record = records[0]
            assert record.data["service"] == "auth"
            assert record.data["version"] == "1.0"
            assert record.data["port"] == 8080


class TestLogRecord:
    """Test LogRecord class."""

    def test_record_creation(self):
        """Test basic record creation."""
        record = LogRecord(
            timestamp=1234567890.123,
            level="INFO",
            logger_name="test",
            message="Test message"
        )

        assert record.timestamp == 1234567890.123
        assert record.level == "INFO"
        assert record.logger_name == "test"
        assert record.message == "Test message"

    def test_record_to_dict(self):
        """Test record conversion to dictionary."""
        record = LogRecord(
            timestamp=1234567890.123,
            level="INFO", 
            logger_name="test",
            message="Test message",
            data={"key": "value"}
        )

        data = record.to_dict()
        assert isinstance(data, dict)
        assert data["timestamp"] == 1234567890.123
        assert data["level"] == "INFO"
        assert data["data"]["key"] == "value"

    def test_record_to_json(self):
        """Test record conversion to JSON."""
        record = LogRecord(
            timestamp=1234567890.123,
            level="INFO",
            logger_name="test", 
            message="Test message"
        )

        json_str = record.to_json()
        assert isinstance(json_str, str)
        assert "timestamp" in json_str
        assert "INFO" in json_str

    def test_record_to_logfmt(self):
        """Test record conversion to logfmt."""
        record = LogRecord(
            timestamp=1234567890.123,
            level="INFO",
            logger_name="test",
            message="Test message",
            data={"user_id": 123}
        )

        logfmt_str = record.to_logfmt()
        assert isinstance(logfmt_str, str)
        assert "timestamp=1234567890.123" in logfmt_str
        assert "level=INFO" in logfmt_str
        assert "user_id=123" in logfmt_str


class TestConfiguration:
    """Test configuration system."""

    def test_basic_configuration(self):
        """Test basic configuration."""
        micktrace.configure(level="DEBUG", format="json")

        config = micktrace.get_configuration()
        assert config.level == "DEBUG"
        assert config.format == "json"
        assert config.is_configured is True

    def test_handler_configuration(self):
        """Test handler configuration."""
        micktrace.configure(
            level="INFO",
            handlers=[
                {"type": "console", "level": "INFO"},
                {"type": "file", "path": "test.log", "level": "WARNING"}
            ]
        )

        config = micktrace.get_configuration()
        assert len(config.handlers) == 2
        assert config.handlers[0].type == "console"
        assert config.handlers[1].type == "file"


@pytest.mark.asyncio
class TestAsyncLogging:
    """Test async logging functionality."""

    async def test_async_context(self):
        """Test async context propagation."""
        with capture_logs() as capture:
            micktrace.configure(level="INFO", handlers=["memory"])
            logger = micktrace.get_logger("test.async")

            async with micktrace.acontext(task_id="task_123"):
                logger.info("Async task started")
                await asyncio.sleep(0.001)  # Simulate async work
                logger.info("Async task completed")

            records = capture.get_records()
            assert len(records) == 2

            for record in records:
                assert record.data["task_id"] == "task_123"


if __name__ == "__main__":
    pytest.main([__file__])
