#!/usr/bin/env python3
"""
Basic Micktrace Example - Demonstrates core features with error handling
"""

import sys
import os
from pathlib import Path

# Add src to path for running from source
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import micktrace
except ImportError as e:
    print(f"Failed to import micktrace: {e}")
    sys.exit(1)


def demonstrate_basic_logging():
    """Demonstrate basic logging features."""
    print("=== Basic Logging Demo ===")

    # Configure micktrace for applications
    micktrace.configure(level="INFO", format="structured")

    # Get a logger
    logger = micktrace.get_logger(__name__)

    # Basic logging calls
    logger.info("Application starting", component="main", version="1.0.0")

    # Structured logging with additional data
    logger.info("User logged in", 
                user_id=123, 
                username="alice", 
                ip_address="192.168.1.100",
                success=True)

    # Different log levels
    logger.debug("Debug information", details="hidden unless debug enabled")
    logger.warning("Something suspicious", threat_level="low", action_required=True)
    logger.error("An error occurred", error_code=500, retryable=True, component="database")

    print("✅ Basic logging completed successfully!")


def demonstrate_context():
    """Demonstrate context propagation."""
    logger = micktrace.get_logger("demo.context")

    print("=== Context Demo ===")

    # Set context for a request
    with micktrace.context(request_id="req_12345", user_id=456, session="sess_789"):
        logger.info("Processing request", operation="get_user_profile")
        logger.info("Database query executed", table="users", duration_ms=45)
        logger.info("Request processed successfully", status_code=200)

    print("✅ Context demo completed successfully!")


def demonstrate_bound_logger():
    """Demonstrate bound logger."""
    logger = micktrace.get_logger("demo.bound")

    print("=== Bound Logger Demo ===")

    # Create a logger bound with common context
    service_logger = logger.bind(service="payment-service", version="2.1.0", environment="production")

    # All logs from this bound logger include the service context
    service_logger.info("Payment processing started", amount=99.99, currency="USD")
    service_logger.info("Payment validated", payment_id="pay_123", provider="stripe")
    service_logger.info("Payment completed", transaction_id="txn_456", fee=2.99)

    # Can create further bound loggers
    request_logger = service_logger.bind(request_id="req_789", customer_id="cust_123")
    request_logger.info("Customer payment history retrieved", count=5)

    print("✅ Bound logger demo completed successfully!")


def demonstrate_exception_handling():
    """Demonstrate exception logging."""
    logger = micktrace.get_logger("demo.exceptions")

    print("=== Exception Handling Demo ===")

    try:
        # Simulate an error
        raise ValueError("This is a demonstration exception")
    except ValueError as e:
        logger.exception("Caught demonstration exception", 
                        error_type="ValueError",
                        user_action="create_account",
                        severity="low")

    print("✅ Exception handling demo completed successfully!")


def demonstrate_different_levels():
    """Demonstrate different log levels."""
    logger = micktrace.get_logger("demo.levels")

    print("=== Log Levels Demo ===")

    # Configure to show all levels
    micktrace.configure(level="DEBUG")

    logger.debug("Debug: Detailed diagnostic information", function="process_data", line=42)
    logger.info("Info: General application flow", checkpoint="user_authenticated")
    logger.warning("Warning: Something unexpected happened", issue="rate_limit_approaching")
    logger.error("Error: Something went wrong", error="database_connection_failed")
    logger.critical("Critical: System is in critical state", alert="service_down")

    print("✅ Log levels demo completed successfully!")


def main():
    """Main function demonstrating micktrace capabilities."""
    print("🚀 Micktrace Basic Example - Comprehensive Demo")
    print("=" * 60)

    try:
        demonstrate_basic_logging()
        print()

        demonstrate_context()
        print()

        demonstrate_bound_logger()
        print()

        demonstrate_exception_handling()
        print()

        demonstrate_different_levels()
        print()

        print("🎉 All demonstrations completed successfully!")
        print("✅ Micktrace is working perfectly!")

    except Exception as e:
        print(f"❌ Error occurred during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
