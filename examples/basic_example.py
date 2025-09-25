#!/usr/bin/env python3
"""
Basic Micktrace Example

Demonstrates the core features of micktrace logging.
"""

import asyncio
import micktrace

# Configure micktrace for this application
micktrace.configure(
    level="INFO",
    format="structured",
    handlers=[
        {"type": "console", "level": "INFO"},
        {"type": "file", "path": "example.log", "level": "DEBUG"}
    ],
    context={
        "service": "example-app",
        "version": "1.0.0"
    }
)

# Get a logger for this module
logger = micktrace.get_logger(__name__)


def demonstrate_basic_logging():
    """Demonstrate basic logging features."""
    logger.info("Application starting", component="main")

    # Structured logging with additional data
    logger.info("User logged in", 
                user_id=123, 
                username="alice", 
                ip_address="192.168.1.100")

    # Different log levels
    logger.debug("Debug information", details="hidden in production")
    logger.warning("Something suspicious", threat_level="low")
    logger.error("An error occurred", error_code=500, retryable=True)

    # Exception logging
    try:
        raise ValueError("Something went wrong!")
    except ValueError:
        logger.exception("Caught an exception")


def demonstrate_context():
    """Demonstrate context propagation."""
    # Set context for a request
    with micktrace.context(request_id="req_12345", user_id=456):
        logger.info("Processing request")

        # All logs within this context will include request_id and user_id
        process_data()
        save_results()


def process_data():
    """Process some data (with context)."""
    logger.info("Processing data", operation="transform")
    logger.info("Data processed", records_count=1000)


def save_results():
    """Save results (with context).""" 
    logger.info("Saving results", destination="database")
    logger.info("Results saved", rows_inserted=1000)


async def demonstrate_async():
    """Demonstrate async logging and tracing."""
    logger.info("Starting async operations")

    # Async context
    async with micktrace.acontext(operation_id="op_789"):
        await process_async_data()
        await send_notifications()

    # Timing operations
    async with micktrace.atimer("database_query") as timer:
        await asyncio.sleep(0.1)  # Simulate database call
        logger.info("Query completed", rows=50)


async def process_async_data():
    """Process data asynchronously."""
    logger.info("Processing async data")
    await asyncio.sleep(0.05)  # Simulate work
    logger.info("Async data processed")


async def send_notifications():
    """Send notifications asynchronously."""
    logger.info("Sending notifications", count=3)
    await asyncio.sleep(0.02)  # Simulate network call
    logger.info("Notifications sent")


def demonstrate_bound_logger():
    """Demonstrate bound logger."""
    # Create a logger bound with common context
    service_logger = logger.bind(service="payment-service", version="2.1.0")

    # All logs from this bound logger include the service context
    service_logger.info("Payment processing started", amount=99.99)
    service_logger.info("Payment validated", payment_id="pay_123")
    service_logger.info("Payment completed", transaction_id="txn_456")


def main():
    """Main function."""
    logger.info("=== Micktrace Example Starting ===")

    demonstrate_basic_logging()
    logger.info("--- Basic logging demo complete ---")

    demonstrate_context()
    logger.info("--- Context demo complete ---")

    demonstrate_bound_logger()
    logger.info("--- Bound logger demo complete ---")

    # Run async demo
    asyncio.run(demonstrate_async())
    logger.info("--- Async demo complete ---")

    logger.info("=== Micktrace Example Complete ===")

    print("Check 'example.log' for the complete log output!")


if __name__ == "__main__":
    main()
