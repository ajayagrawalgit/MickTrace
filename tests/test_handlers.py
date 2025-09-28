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
        micktrace.configure(
            level="INFO",
            handlers=[{"type": "console"}]
        )
        
        logger = micktrace.get_logger("console_test")
        logger.info("Console handler test message")
        # Test passes if no exceptions are raised

    def test_memory_handler_creation(self):
        """Test memory handler creation."""
        micktrace.configure(
            level="INFO",
            handlers=[{"type": "memory"}]
        )
        
        logger = micktrace.get_logger("memory_test")
        logger.info("Memory handler test message")
        # Test passes if no exceptions are raised

    def test_null_handler_creation(self):
        """Test null handler creation."""
        micktrace.configure(
            level="INFO",
            handlers=[{"type": "null"}]
        )
        
        logger = micktrace.get_logger("null_test")
        logger.info("Null handler test message")
        # Test passes if no exceptions are raised

    def test_file_handler_creation(self):
        """Test file handler creation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            micktrace.configure(
                level="INFO",
                handlers=[{
                    "type": "file",
                    "config": {"path": tmp_path}
                }]
            )
            
            logger = micktrace.get_logger("file_test")
            logger.info("File handler test message")
            
            # Verify file was created and has content
            assert os.path.exists(tmp_path)
            with open(tmp_path, 'r') as f:
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
                    {"type": "file", "config": {"path": tmp_path}}
                ]
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
            handlers=[{
                "type": "file",
                "path": "test1.log"  # Direct in handler config
            }]
        )
        
        # Test with nested config
        micktrace.configure(
            level="INFO", 
            handlers=[{
                "type": "file",
                "config": {
                    "path": "test2.log"  # Nested in config
                }
            }]
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
                handlers=[{
                    "type": "cloudwatch",
                    "config": {
                        "log_group": "test",
                        "log_stream": "test",
                        "region": "us-east-1"
                    }
                }]
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
                handlers=[{
                    "type": "azure",
                    "config": {
                        "connection_string": "test"
                    }
                }]
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
                handlers=[{
                    "type": "stackdriver",
                    "config": {
                        "project_id": "test",
                        "log_name": "test"
                    }
                }]
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
                {"type": "memory"}  # Another valid handler
            ]
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
                    {"type": "file", "level": "DEBUG", "config": {"path": tmp_path}}
                ]
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
            handlers=[{
                "type": "file",
                "config": {"path": "/invalid/path/that/does/not/exist/test.log"}
            }]
        )
        
        logger = micktrace.get_logger("error_test")
        logger.info("Test message with invalid file handler")
        # Should not crash even if file handler fails

    def test_handler_runtime_errors(self):
        """Test that runtime handler errors don't crash logging."""
        micktrace.configure(
            level="INFO",
            handlers=[
                {"type": "console"},  # Fallback handler
                {"type": "memory"}
            ]
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
                level="INVALID_LEVEL",
                handlers=[{"type": "invalid_type"}]
            )
        except Exception:
            pass  # Expected to handle gracefully
        
        # Should be able to reconfigure successfully
        micktrace.configure(
            level="INFO",
            handlers=[{"type": "console"}]
        )
        
        logger = micktrace.get_logger("recovery_test")
        logger.info("Recovery test message")
        # Should work after recovery


class TestHandlerPerformance:
    """Test handler performance characteristics."""

    def test_null_handler_performance(self):
        """Test null handler performance (should be very fast)."""
        micktrace.configure(
            level="INFO",
            handlers=[{"type": "null"}]
        )
        
        logger = micktrace.get_logger("performance_test")
        
        # Log many messages quickly
        for i in range(1000):
            logger.info("Performance test message", iteration=i)
        
        # Should complete quickly without issues

    def test_memory_handler_capacity(self):
        """Test memory handler with many messages."""
        micktrace.configure(
            level="INFO",
            handlers=[{"type": "memory"}]
        )
        
        logger = micktrace.get_logger("capacity_test")
        
        # Log many messages
        for i in range(100):
            logger.info("Capacity test message", iteration=i, data={"key": f"value_{i}"})
        
        # Should handle all messages without issues
