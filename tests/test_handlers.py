"""
Test handler functionality and creation.
Tests all handler types, configuration, and error handling.
"""

import os
import tempfile
import pytest
import micktrace


class TestHandlerCreation:
    """Test handler creation and configuration."""

    def setup_method(self):
        """Setup for each test."""
        micktrace.clear_context()

    def test_console_handler_creation(self):
        """Test console handler creation."""
        micktrace.configure(level="INFO", handlers=[{"type": "console"}])

        logger = micktrace.get_logger("console_test")
        logger.info("Console handler test message")
        # Test passes if no exceptions are raised

    def test_memory_handler_creation(self):
        """Test memory handler creation."""
        micktrace.configure(level="INFO", handlers=[{"type": "memory"}])

        logger = micktrace.get_logger("memory_test")
        logger.info("Memory handler test message")
        # Test passes if no exceptions are raised

    def test_null_handler_creation(self):
        """Test null handler creation."""
        micktrace.configure(level="INFO", handlers=[{"type": "null"}])

        logger = micktrace.get_logger("null_test")
        logger.info("Null handler test message")
        # Test passes if no exceptions are raised

    def test_file_handler_creation(self):
        """Test file handler creation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            micktrace.configure(
                level="INFO", handlers=[{"type": "file", "config": {"path": tmp_path}}]
            )

            logger = micktrace.get_logger("file_test")
            logger.info("File handler test message")

            # Verify file was created and has content
            assert os.path.exists(tmp_path)
            with open(tmp_path, "r") as f:
                content = f.read()
                assert "File handler test message" in content

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_multiple_handlers(self):
        """Test configuration with multiple handlers."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            micktrace.configure(
                level="INFO",
                handlers=[
                    {"type": "console"},
                    {"type": "memory"},
                    {"type": "file", "config": {"path": tmp_path}},
                ],
            )

            logger = micktrace.get_logger("multi_handler_test")
            logger.info("Multiple handlers test message")

            # Verify file handler worked
            assert os.path.exists(tmp_path)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_handler_config_variations(self):
        """Test different handler configuration formats."""
        # Test with config in handler dict
        micktrace.configure(
            level="INFO",
            handlers=[
                # Direct in handler config
                {"type": "file", "path": "test1.log"}
            ],
        )

        # Test with nested config
        micktrace.configure(
            level="INFO",
            handlers=[
                {"type": "file", "config": {"path": "test2.log"}}  # Nested in config
            ],
        )

        logger = micktrace.get_logger("config_test")
        logger.info("Handler config test")

        # Clean up
        for log_file in ["test1.log", "test2.log"]:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_cloud_handler_graceful_failure(self):
        """Test that cloud handlers fail gracefully without dependencies."""
        # CloudWatch handler should not crash without boto3
        try:
            micktrace.configure(
                level="INFO",
                handlers=[
                    {
                        "type": "cloudwatch",
                        "config": {
                            "log_group": "test",
                            "log_stream": "test",
                            "region": "us-east-1",
                        },
                    }
                ],
            )

            logger = micktrace.get_logger("cloudwatch_test")
            logger.info("CloudWatch test message")
            # Should not crash even if AWS dependencies are missing

        except ImportError:
            # Expected if dependencies are missing
            pass

    def test_azure_handler_graceful_failure(self):
        """Test that Azure handler fails gracefully without dependencies."""
        try:
            micktrace.configure(
                level="INFO",
                handlers=[{"type": "azure", "config": {
                    "connection_string": "test"}}],
            )

            logger = micktrace.get_logger("azure_test")
            logger.info("Azure test message")
            # Should not crash even if Azure dependencies are missing

        except ImportError:
            # Expected if dependencies are missing
            pass

    def test_stackdriver_handler_graceful_failure(self):
        """Test that Stackdriver handler fails gracefully without dependencies."""
        try:
            micktrace.configure(
                level="INFO",
                handlers=[
                    {
                        "type": "stackdriver",
                        "config": {"project_id": "test", "log_name": "test"},
                    }
                ],
            )

            logger = micktrace.get_logger("stackdriver_test")
            logger.info("Stackdriver test message")
            # Should not crash even if GCP dependencies are missing

        except ImportError:
            # Expected if dependencies are missing
            pass

    def test_invalid_handler_type(self):
        """Test handling of invalid handler types."""
        # Invalid handler type should not crash the system
        micktrace.configure(
            level="INFO",
            handlers=[
                {"type": "console"},  # Valid handler
                {"type": "invalid_handler_type"},  # Invalid handler
                {"type": "memory"},  # Another valid handler
            ],
        )

        logger = micktrace.get_logger("invalid_handler_test")
        logger.info("Test with invalid handler")
        # Should work with valid handlers despite invalid one

    def test_handler_with_different_levels(self):
        """Test handlers with different log levels."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            micktrace.configure(
                level="DEBUG",
                handlers=[
                    {"type": "console", "level": "INFO"},
                    {"type": "file", "level": "DEBUG",
                        "config": {"path": tmp_path}},
                ],
            )

            logger = micktrace.get_logger("level_test")
            logger.debug("Debug message")
            logger.info("Info message")
            logger.error("Error message")

            # File should have all messages, console should have INFO and above
            assert os.path.exists(tmp_path)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestHandlerErrorHandling:
    """Test handler error handling and resilience."""

    def test_handler_creation_errors(self):
        """Test that handler creation errors don't crash the system."""
        # Test with invalid file path
        micktrace.configure(
            level="INFO",
            handlers=[
                {
                    "type": "file",
                    "config": {"path": "/invalid/path/that/does/not/exist/test.log"},
                }
            ],
        )

        logger = micktrace.get_logger("error_test")
        logger.info("Test message with invalid file handler")
        # Should not crash even if file handler fails

    def test_handler_runtime_errors(self):
        """Test that runtime handler errors don't crash logging."""
        micktrace.configure(
            level="INFO",
            handlers=[{"type": "console"}, {
                "type": "memory"}],  # Fallback handler
        )

        logger = micktrace.get_logger("runtime_error_test")

        # Simulate various logging scenarios that might cause errors
        logger.info("Normal message")
        logger.info("Message with special chars: üñíçødé")
        logger.info("Message with None value", none_value=None)
        logger.info("Message with large data", large_data="x" * 10000)

        # All should complete without crashing

    def test_configuration_error_recovery(self):
        """Test recovery from configuration errors."""
        # Start with invalid configuration
        try:
            micktrace.configure(
                level="INVALID_LEVEL", handlers=[{"type": "invalid_type"}]
            )
        except Exception:
            pass  # Expected to handle gracefully

        # Should be able to reconfigure successfully
        micktrace.configure(level="INFO", handlers=[{"type": "console"}])

        logger = micktrace.get_logger("recovery_test")
        logger.info("Recovery test message")
        # Should work after recovery


class TestHandlerPerformance:
    """Test handler performance characteristics."""

    def test_null_handler_performance(self):
        """Test null handler performance (should be very fast)."""
        micktrace.configure(level="INFO", handlers=[{"type": "null"}])

        logger = micktrace.get_logger("performance_test")

        # Log many messages quickly
        for i in range(1000):
            logger.info("Performance test message", iteration=i)

        # Should complete quickly without issues

    def test_memory_handler_capacity(self):
        """Test memory handler with many messages."""
        micktrace.configure(level="INFO", handlers=[{"type": "memory"}])

        logger = micktrace.get_logger("capacity_test")

        # Log many messages
        for i in range(100):
            logger.info(
                "Capacity test message", iteration=i, data={"key": f"value_{i}"}
            )

        # Should handle all messages without issues


class TestConsoleHandlerAdditionalParameters:
    """Test console handler's ability to display additional parameters."""

    def setup_method(self):
        """Setup for each test."""
        micktrace.clear_context()

    def test_console_handler_with_single_parameter(self, capsys):
        """Test console handler displays single additional parameter."""
        from micktrace.handlers.console import ConsoleHandler
        from micktrace.types import LogRecord
        import time

        # Create console handler directly
        handler = ConsoleHandler()

        # Create log record with additional parameter
        record = LogRecord(
            timestamp=1234567890.123,
            level="INFO",
            logger_name="test",
            message="Test message",
            data={"info": "hey"}
        )

        # Emit the record
        handler.emit(record)

        # Capture output
        captured = capsys.readouterr()

        # Verify output contains both message and parameter
        assert "Test message" in captured.err
        assert "info=hey" in captured.err
        assert "1234567890.123 INFO" in captured.err

    def test_console_handler_with_multiple_parameters(self, capsys):
        """Test console handler displays multiple additional parameters."""
        from micktrace.handlers.console import ConsoleHandler
        from micktrace.types import LogRecord

        handler = ConsoleHandler()

        record = LogRecord(
            timestamp=1234567890.456,
            level="WARNING",
            logger_name="test",
            message="Multiple params test",
            data={"user_id": 12345, "action": "login", "success": True}
        )

        handler.emit(record)
        captured = capsys.readouterr()

        # Verify all parameters are present
        assert "Multiple params test" in captured.err
        assert "user_id=12345" in captured.err
        assert "action=login" in captured.err
        assert "success=True" in captured.err

    def test_console_handler_without_additional_parameters(self, capsys):
        """Test console handler works normally without additional parameters."""
        from micktrace.handlers.console import ConsoleHandler
        from micktrace.types import LogRecord

        handler = ConsoleHandler()

        record = LogRecord(
            timestamp=1234567890.789,
            level="ERROR",
            logger_name="test",
            message="Simple error message",
            data={}
        )

        handler.emit(record)
        captured = capsys.readouterr()

        # Should only contain basic log info
        assert "Simple error message" in captured.err
        assert "1234567890.789 ERROR" in captured.err
        # Should not have any extra parameters
        lines = captured.err.strip().split('\n')
        assert len(lines) == 1
        assert "=" not in captured.err  # No key=value pairs

    def test_console_handler_filters_timestamp_iso(self, capsys):
        """Test console handler filters out internal timestamp_iso field."""
        from micktrace.handlers.console import ConsoleHandler
        from micktrace.types import LogRecord

        handler = ConsoleHandler()

        record = LogRecord(
            timestamp=1234567890.999,
            level="DEBUG",
            logger_name="test",
            message="Test with timestamp_iso",
            data={
                "info": "visible",
                "timestamp_iso": "2025-01-01T00:00:00",
                "user": "test"
            }
        )

        handler.emit(record)
        captured = capsys.readouterr()

        # Should contain visible parameters but not timestamp_iso
        assert "info=visible" in captured.err
        assert "user=test" in captured.err
        assert "timestamp_iso" not in captured.err

    def test_console_handler_with_complex_data_types(self, capsys):
        """Test console handler with various data types."""
        from micktrace.handlers.console import ConsoleHandler
        from micktrace.types import LogRecord

        handler = ConsoleHandler()

        record = LogRecord(
            timestamp=1234567890.111,
            level="INFO",
            logger_name="test",
            message="Complex data types",
            data={
                "string_val": "hello",
                "int_val": 42,
                "float_val": 3.14,
                "bool_val": False,
                "none_val": None,
                "dict_val": {"nested": "value"},
                "list_val": [1, 2, 3]
            }
        )

        handler.emit(record)
        captured = capsys.readouterr()

        # Verify all data types are converted to strings properly
        assert "string_val=hello" in captured.err
        assert "int_val=42" in captured.err
        assert "float_val=3.14" in captured.err
        assert "bool_val=False" in captured.err
        assert "none_val=None" in captured.err
        assert "dict_val=" in captured.err  # Dict should be converted to string
        assert "list_val=" in captured.err  # List should be converted to string

    def test_console_handler_error_handling(self, capsys):
        """Test console handler handles errors gracefully."""
        from micktrace.handlers.console import ConsoleHandler
        from micktrace.types import LogRecord

        handler = ConsoleHandler()

        # Test with potentially problematic data
        record = LogRecord(
            timestamp=1234567890.222,
            level="ERROR",
            logger_name="test",
            message="Error handling test",
            data={"special_chars": "üñíçødé", "large_data": "x" * 1000}
        )

        # Should not raise exception
        try:
            handler.emit(record)
            captured = capsys.readouterr()
            assert "Error handling test" in captured.err
        except Exception as e:
            pytest.fail(f"Console handler should not raise exception: {e}")


class TestHandlerConsistency:
    """Test consistency between console and file handlers."""

    def setup_method(self):
        """Setup for each test."""
        micktrace.clear_context()

    def test_console_and_file_handler_parameter_consistency(self):
        """Test that console and file handlers handle additional parameters consistently."""
        import tempfile
        import json
        from micktrace.handlers.console import ConsoleHandler
        from micktrace.handlers.file import FileHandler
        from micktrace.types import LogRecord

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_file = f.name

        try:
            # Create handlers
            console_handler = ConsoleHandler()
            file_handler = FileHandler(filename=temp_file)

            # Create test record with additional parameters
            record = LogRecord(
                timestamp=1234567890.555,
                level="INFO",
                logger_name="consistency_test",
                message="Consistency test message",
                data={"param1": "value1", "param2": 42, "param3": True}
            )

            # Emit to both handlers
            console_handler.emit(record)
            file_handler.emit(record)

            # Read file content
            with open(temp_file, 'r') as f:
                file_content = f.read().strip()

            # Parse JSON from file
            file_data = json.loads(file_content)

            # Verify file handler stored all data
            assert file_data["message"] == "Consistency test message"
            assert file_data["data"]["param1"] == "value1"
            assert file_data["data"]["param2"] == 42
            assert file_data["data"]["param3"] == True

            # Console handler should have displayed the parameters
            # (We can't easily capture stderr in this test, but the structure is tested above)

        finally:
            # Clean up
            import os
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_integrated_logger_with_additional_parameters(self):
        """Test integrated logger functionality with additional parameters."""
        import tempfile
        import json

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_file = f.name

        try:
            # Configure logger with both handlers
            micktrace.configure(
                level="DEBUG",
                handlers=[
                    {"type": "console", "level": "INFO"},
                    {"type": "file", "level": "DEBUG",
                        "config": {"path": temp_file}}
                ]
            )

            logger = micktrace.get_logger("integration_test")

            # Test various logging scenarios
            logger.info("Simple message")
            logger.info("Message with single param", user="john")
            logger.warning("Message with multiple params",
                           user_id=123, action="login", success=True, ip="192.168.1.1")
            logger.error("Error with context",
                         error_code=500, module="auth", details={"reason": "timeout"})

            # Verify file contains all the data
            with open(temp_file, 'r') as f:
                lines = f.readlines()

            # Should have 4 log entries
            assert len(lines) == 4

            # Parse and verify each entry
            for line in lines:
                data = json.loads(line.strip())
                assert "timestamp" in data
                assert "level" in data
                assert "message" in data
                assert "data" in data

            # Verify specific entries
            line2_data = json.loads(lines[1].strip())
            assert line2_data["data"]["user"] == "john"

            line3_data = json.loads(lines[2].strip())
            assert line3_data["data"]["user_id"] == 123
            assert line3_data["data"]["action"] == "login"
            assert line3_data["data"]["success"] == True

        finally:
            # Clean up
            import os
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestConsoleHandlerEdgeCases:
    """Test edge cases for console handler additional parameters."""

    def setup_method(self):
        """Setup for each test."""
        micktrace.clear_context()

    def test_console_handler_with_empty_data(self, capsys):
        """Test console handler with empty data dictionary."""
        from micktrace.handlers.console import ConsoleHandler
        from micktrace.types import LogRecord

        handler = ConsoleHandler()

        record = LogRecord(
            timestamp=1234567890.0,
            level="INFO",
            logger_name="test",
            message="Empty data test",
            data={}
        )

        handler.emit(record)
        captured = capsys.readouterr()

        # Should only show basic log info, no extra parameters
        assert "Empty data test" in captured.err
        assert "=" not in captured.err

    def test_console_handler_with_none_data(self, capsys):
        """Test console handler when data is None."""
        from micktrace.handlers.console import ConsoleHandler
        from micktrace.types import LogRecord

        handler = ConsoleHandler()

        # Manually create record with None data (edge case)
        record = LogRecord(
            timestamp=1234567890.0,
            level="INFO",
            logger_name="test",
            message="None data test"
        )
        record.data = None  # Force None data

        # Should handle gracefully without crashing
        try:
            handler.emit(record)
            captured = capsys.readouterr()
            assert "None data test" in captured.err
        except Exception as e:
            pytest.fail(f"Should handle None data gracefully: {e}")

    def test_console_handler_with_special_characters_in_keys_and_values(self, capsys):
        """Test console handler with special characters in parameter keys and values."""
        from micktrace.handlers.console import ConsoleHandler
        from micktrace.types import LogRecord

        handler = ConsoleHandler()

        record = LogRecord(
            timestamp=1234567890.0,
            level="INFO",
            logger_name="test",
            message="Special chars test",
            data={
                "key with spaces": "value with spaces",
                "key=with=equals": "value=with=equals",
                "unicode_key": "üñíçødé_value",
                "quotes": 'value"with"quotes',
                "newlines": "value\nwith\nnewlines"
            }
        )

        handler.emit(record)
        captured = capsys.readouterr()

        # Should handle all special characters without crashing
        assert "Special chars test" in captured.err
        # All parameters should be present in some form
        assert "key with spaces=" in captured.err
        assert "unicode_key=" in captured.err
