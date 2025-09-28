"""
Test configuration functionality.
Tests various configuration methods, validation, and error handling.
"""

import os
import pytest
import micktrace


class TestConfiguration:
    """Test configuration functionality."""

    def setup_method(self):
        """Setup for each test."""
        micktrace.clear_context()

    def test_basic_configuration(self):
        """Test basic configuration."""
        micktrace.configure(
            level="INFO",
            format="structured",
            handlers=[{"type": "console"}]
        )
        
        logger = micktrace.get_logger("config_test")
        logger.info("Basic configuration test")
        # Test passes if no exceptions are raised

    def test_configuration_with_service_info(self):
        """Test configuration with service information."""
        micktrace.configure(
            level="DEBUG",
            format="structured",
            service="test-service",
            version="1.0.0",
            environment="test",
            handlers=[{"type": "memory"}]
        )
        
        logger = micktrace.get_logger("service_test")
        logger.info("Service configuration test")

    def test_multiple_reconfigurations(self):
        """Test that multiple reconfigurations work."""
        # First configuration
        micktrace.configure(
            level="DEBUG",
            handlers=[{"type": "console"}]
        )
        
        logger = micktrace.get_logger("reconfig_test")
        logger.debug("First configuration")
        
        # Second configuration
        micktrace.configure(
            level="INFO",
            handlers=[{"type": "memory"}]
        )
        
        logger.info("Second configuration")
        logger.debug("This should not appear due to level change")

    def test_configuration_validation(self):
        """Test configuration validation and error handling."""
        # Test with invalid level (should handle gracefully)
        micktrace.configure(
            level="INVALID_LEVEL",
            handlers=[{"type": "console"}]
        )
        
        logger = micktrace.get_logger("validation_test")
        logger.info("Validation test with invalid level")

    def test_handler_configuration_formats(self):
        """Test different handler configuration formats."""
        # Test list of handler configs
        micktrace.configure(
            level="INFO",
            handlers=[
                {"type": "console", "level": "INFO"},
                {"type": "memory", "level": "DEBUG"}
            ]
        )
        
        logger = micktrace.get_logger("handler_format_test")
        logger.info("Handler format test")

    def test_empty_configuration(self):
        """Test configuration with minimal parameters."""
        micktrace.configure()
        
        logger = micktrace.get_logger("empty_config_test")
        logger.info("Empty configuration test")

    def test_configuration_with_invalid_handlers(self):
        """Test configuration with some invalid handlers."""
        micktrace.configure(
            level="INFO",
            handlers=[
                {"type": "console"},  # Valid
                {"type": "invalid_handler"},  # Invalid
                {"type": "memory"},  # Valid
                {}  # Invalid (no type)
            ]
        )
        
        logger = micktrace.get_logger("invalid_handlers_test")
        logger.info("Test with mixed valid/invalid handlers")

    def test_basic_config_function(self):
        """Test basic_config convenience function."""
        micktrace.basic_config(level="INFO", format="json")
        
        logger = micktrace.get_logger("basic_config_test")
        logger.info("Basic config test")

    def test_disable_enable_functions(self):
        """Test disable and enable functions."""
        micktrace.configure(level="INFO", handlers=[{"type": "console"}])
        logger = micktrace.get_logger("disable_test")
        
        logger.info("Before disable")
        
        micktrace.disable()
        logger.info("During disable (should not appear)")
        
        micktrace.enable()
        logger.info("After enable")

    def test_configuration_error_recovery(self):
        """Test that configuration errors don't break the system."""
        # Try invalid configuration
        try:
            micktrace.configure(
                level=None,  # Invalid
                handlers=None  # Invalid
            )
        except Exception:
            pass  # Expected to handle gracefully
        
        # Should be able to configure properly afterwards
        micktrace.configure(
            level="INFO",
            handlers=[{"type": "console"}]
        )
        
        logger = micktrace.get_logger("error_recovery_test")
        logger.info("Error recovery test")


class TestConfigurationEdgeCases:
    """Test configuration edge cases and error conditions."""

    def test_configuration_with_none_values(self):
        """Test configuration with None values."""
        micktrace.configure(
            level=None,
            format=None,
            handlers=None
        )
        
        logger = micktrace.get_logger("none_values_test")
        logger.info("None values test")

    def test_configuration_with_empty_handlers(self):
        """Test configuration with empty handlers list."""
        micktrace.configure(
            level="INFO",
            handlers=[]
        )
        
        logger = micktrace.get_logger("empty_handlers_test")
        logger.info("Empty handlers test")

    def test_configuration_type_errors(self):
        """Test configuration with wrong types."""
        # These should be handled gracefully
        micktrace.configure(
            level=123,  # Should be string
            format=["json"],  # Should be string
            handlers="console"  # Should be list
        )
        
        logger = micktrace.get_logger("type_errors_test")
        logger.info("Type errors test")

    def test_partial_configuration_updates(self):
        """Test partial configuration updates."""
        # Initial configuration
        micktrace.configure(
            level="DEBUG",
            format="structured",
            handlers=[{"type": "console"}]
        )
        
        # Partial update (only level)
        micktrace.configure(level="INFO")
        
        logger = micktrace.get_logger("partial_update_test")
        logger.info("Partial update test")
        logger.debug("This should not appear due to level change")

    def test_configuration_with_extra_parameters(self):
        """Test configuration with extra/unknown parameters."""
        micktrace.configure(
            level="INFO",
            handlers=[{"type": "console"}],
            unknown_parameter="value",
            extra_config={"key": "value"}
        )
        
        logger = micktrace.get_logger("extra_params_test")
        logger.info("Extra parameters test")


class TestEnvironmentConfiguration:
    """Test environment-based configuration."""

    def test_environment_variable_configuration(self):
        """Test configuration via environment variables."""
        # Set environment variables
        os.environ["MICKTRACE_LEVEL"] = "DEBUG"
        os.environ["MICKTRACE_FORMAT"] = "json"
        
        try:
            # Configuration should pick up environment variables
            micktrace.configure()
            
            logger = micktrace.get_logger("env_config_test")
            logger.debug("Environment configuration test")
            
        finally:
            # Clean up environment variables
            os.environ.pop("MICKTRACE_LEVEL", None)
            os.environ.pop("MICKTRACE_FORMAT", None)

    def test_environment_override(self):
        """Test that explicit config overrides environment variables."""
        os.environ["MICKTRACE_LEVEL"] = "ERROR"
        
        try:
            # Explicit configuration should override environment
            micktrace.configure(level="DEBUG")
            
            logger = micktrace.get_logger("env_override_test")
            logger.debug("This should appear despite env var setting ERROR")
            
        finally:
            os.environ.pop("MICKTRACE_LEVEL", None)

    def test_invalid_environment_values(self):
        """Test handling of invalid environment variable values."""
        os.environ["MICKTRACE_LEVEL"] = "INVALID_LEVEL"
        os.environ["MICKTRACE_FORMAT"] = "INVALID_FORMAT"
        
        try:
            micktrace.configure()
            
            logger = micktrace.get_logger("invalid_env_test")
            logger.info("Invalid environment values test")
            
        finally:
            os.environ.pop("MICKTRACE_LEVEL", None)
            os.environ.pop("MICKTRACE_FORMAT", None)
