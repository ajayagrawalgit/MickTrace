"""
Basic tests for micktrace functionality with comprehensive error handling.
"""

import sys
import time

try:
    import micktrace
    from micktrace.types import LogLevel, LogRecord
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install micktrace first: pip install -e .")
    exit(1)


def test_logger_creation():
    """Test basic logger creation."""
    try:
        logger = micktrace.get_logger("test")
        assert logger is not None
        assert logger.name == "test"
        return True
    except Exception as e:
        print(f"test_logger_creation failed: {e}")
        return False


def test_log_levels():
    """Test log level enum."""
    try:
        debug = LogLevel.from_string("DEBUG")
        info = LogLevel.from_string("INFO")

        assert debug.value == 10
        assert info.value == 20
        assert debug < info
        return True
    except Exception as e:
        print(f"test_log_levels failed: {e}")
        return False


def test_log_record():
    """Test log record creation."""
    try:
        record = LogRecord(
            timestamp=1234567890.123,
            level="INFO",
            logger_name="test",
            message="Test message",
        )

        assert record.timestamp == 1234567890.123
        assert record.level == "INFO"
        assert record.logger_name == "test"
        assert record.message == "Test message"
        return True
    except Exception as e:
        print(f"test_log_record failed: {e}")
        return False


def test_log_record_serialization():
    """Test log record JSON serialization."""
    try:
        record = LogRecord(
            timestamp=1234567890.123,
            level="INFO",
            logger_name="test",
            message="Test message",
            data={"key": "value"},
        )

        json_str = record.to_json()
        assert isinstance(json_str, str)
        assert "timestamp" in json_str
        assert "INFO" in json_str
        assert "key" in json_str

        logfmt_str = record.to_logfmt()
        assert isinstance(logfmt_str, str)
        assert "level=INFO" in logfmt_str
        return True
    except Exception as e:
        print(f"test_log_record_serialization failed: {e}")
        return False


def test_basic_logging():
    """Test basic logging functionality."""
    try:
        logger = micktrace.get_logger("test.basic")

        # These should not raise any exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        return True
    except Exception as e:
        print(f"test_basic_logging failed: {e}")
        return False


def test_structured_logging():
    """Test structured logging with additional data."""
    try:
        logger = micktrace.get_logger("test.structured")

        # Should not raise exceptions
        logger.info("User login", user_id=123, action="login", success=True)
        logger.error("Database error", error_code=500, table="users", retryable=True)
        return True
    except Exception as e:
        print(f"test_structured_logging failed: {e}")
        return False


def test_bound_logger():
    """Test bound logger functionality."""
    try:
        logger = micktrace.get_logger("test.bound")

        bound = logger.bind(service="auth", version="1.0")
        bound.info("Service started", port=8080)

        # Test chaining
        bound2 = bound.bind(request_id="req_123")
        bound2.info("Request processed")

        assert bound is not None
        assert bound2 is not None
        return True
    except Exception as e:
        print(f"test_bound_logger failed: {e}")
        return False


def test_configuration():
    """Test configuration system."""
    try:
        # Basic configuration should work
        micktrace.configure(
            level="DEBUG", format="structured", handlers=[{"type": "console"}]
        )
        return True
    except Exception as e:
        print(f"test_configuration failed: {e}")
        return False


def test_exception_logging():
    """Test exception logging."""
    try:
        logger = micktrace.get_logger("test.exceptions")

        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("Caught an exception")

        # Should not raise any exceptions during logging
        return True
    except Exception as e:
        print(f"test_exception_logging failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    test_functions = [
        test_logger_creation,
        test_log_levels,
        test_log_record,
        test_log_record_serialization,
        test_basic_logging,
        test_structured_logging,
        test_bound_logger,
        test_configuration,
        test_exception_logging,
    ]

    print("🧪 Running Micktrace comprehensive tests...")
    print("=" * 50)

    passed = 0
    failed = 0

    for test_func in test_functions:
        test_name = test_func.__name__
        try:
            if test_func():
                print(f"✅ {test_name}")
                passed += 1
            else:
                print(f"❌ {test_name}")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            failed += 1

    print("=" * 50)
    print(f"📊 Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"💥 {failed} tests failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
