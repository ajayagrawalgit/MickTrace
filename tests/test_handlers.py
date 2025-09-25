"""
Tests for handler functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import micktrace
from micktrace.handlers.console import ConsoleHandler
from micktrace.handlers.file import FileHandler
from micktrace.handlers.base import MemoryHandler
from micktrace.core.record import LogRecord


class TestMemoryHandler:
    """Test memory handler."""

    def test_memory_handler(self):
        """Test basic memory handler functionality."""
        handler = MemoryHandler(name="test_memory")

        record = LogRecord(
            timestamp=1234567890.123,
            level="INFO",
            logger_name="test",
            message="Test message"
        )

        handler.handle_sync(record)

        records = handler.get_records()
        assert len(records) == 1
        assert records[0] == record

    def test_memory_handler_clear(self):
        """Test memory handler clearing."""
        handler = MemoryHandler(name="test_memory")

        record = LogRecord(
            timestamp=1234567890.123,
            level="INFO",
            logger_name="test",
            message="Test message"
        )

        handler.handle_sync(record)
        assert len(handler.get_records()) == 1

        handler.clear()
        assert len(handler.get_records()) == 0


class TestFileHandler:
    """Test file handler."""

    def test_file_handler(self):
        """Test basic file handler functionality."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_path = f.name

        try:
            handler = FileHandler(name="test_file", path=temp_path)

            record = LogRecord(
                timestamp=1234567890.123,
                level="INFO",
                logger_name="test",
                message="Test message"
            )

            handler.handle_sync(record)

            # Check file content
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "Test message" in content
                assert "INFO" in content

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_file_handler_rotation(self):
        """Test file handler rotation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "test.log"

            # Create handler with small max size for testing
            handler = FileHandler(
                name="test_rotation",
                path=log_path,
                max_size="1KB",  # Very small for testing
                max_count=3
            )

            # Write many records to trigger rotation
            for i in range(100):
                record = LogRecord(
                    timestamp=1234567890.123 + i,
                    level="INFO",
                    logger_name="test",
                    message=f"Test message {i} with some additional content to increase size"
                )
                handler.handle_sync(record)

            # Check that rotation occurred (multiple log files)
            log_files = list(Path(temp_dir).glob("test_*.log*"))
            assert len(log_files) > 1  # Should have rotated files


class TestConsoleHandler:
    """Test console handler."""

    def test_console_handler_creation(self):
        """Test console handler creation."""
        handler = ConsoleHandler(name="test_console")
        assert handler.name == "test_console"
        assert handler.use_smart_streams is True

    def test_console_handler_formatting(self):
        """Test console handler message formatting."""
        handler = ConsoleHandler(name="test_console", rich_format=False)

        record = LogRecord(
            timestamp=1234567890.123,
            level="INFO",
            logger_name="test",
            message="Test message",
            data={"key": "value"}
        )

        formatted = handler._format_plain(record)
        assert "INFO" in formatted
        assert "test" in formatted
        assert "Test message" in formatted


if __name__ == "__main__":
    pytest.main([__file__])
