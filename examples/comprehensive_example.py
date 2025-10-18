"""
MickTrace Comprehensive Example - Production Ready
=================================================

This example demonstrates all core MickTrace features in a simple,
working format suitable for production use.
"""

import asyncio
import time
import micktrace
from uuid import uuid4
from datetime import datetime


def demonstrate_basic_features():
    """Demonstrate basic logging features."""
    print("=== Basic Logging Features ===")

    # Configure logging
    micktrace.configure(
        level="DEBUG", format="structured", handlers=[{"type": "console"}]
    )

    logger = micktrace.get_logger("comprehensive_demo")

    # All log levels
    logger.debug("Debug message", module="demo", details="verbose info")
    logger.info("Info message", status="active", count=42)
    logger.warning("Warning message", usage=85, threshold=90)
    logger.error("Error message", error_code="E001", retryable=True)
    logger.critical("Critical message", impact="high", action_required=True)

    print("✅ Basic features completed!")


def demonstrate_structured_logging():
    """Demonstrate structured logging with rich data."""
    print("\n=== Structured Logging ===")

    logger = micktrace.get_logger("structured_demo")

    # Complex structured data
    user_data = {
        "id": "user_12345",
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "roles": ["admin", "user"],
        "metadata": {
            "last_login": datetime.now().isoformat(),
            "login_count": 42,
            "preferences": {"theme": "dark", "notifications": True},
        },
    }

    logger.info("User profile loaded", **user_data)

    # API request logging
    logger.info(
        "API request processed",
        method="POST",
        endpoint="/api/users",
        status_code=201,
        response_time_ms=145.2,
        request_id=str(uuid4()),
        client_ip="192.168.1.100",
    )

    print("✅ Structured logging completed!")


def demonstrate_bound_loggers():
    """Demonstrate bound loggers for context."""
    print("\n=== Bound Loggers ===")

    base_logger = micktrace.get_logger("bound_demo")

    # Create service-level bound logger
    service_logger = base_logger.bind(
        service="user-service", version="2.1.0", environment="production"
    )

    # Create request-level bound logger
    request_logger = service_logger.bind(
        request_id=str(uuid4()), user_id="user_67890", operation="update_profile"
    )

    # All context is automatically included
    request_logger.info("Request started")
    request_logger.info("Validating input data", fields=["email", "name"])
    request_logger.info("Updating database record", table="users")
    request_logger.info("Request completed", duration_ms=234)

    print("✅ Bound loggers completed!")


def demonstrate_error_handling():
    """Demonstrate error handling and exception logging."""
    print("\n=== Error Handling ===")

    logger = micktrace.get_logger("error_demo").bind(
        component="payment_processor", version="1.0.0"
    )

    # Simulate various error scenarios
    try:
        # Simulate a network error
        raise ConnectionError("Payment gateway unreachable")
    except Exception as e:
        logger.error(
            "Payment processing failed",
            error_type=type(e).__name__,
            error_message=str(e),
            payment_id="pay_12345",
            retry_count=3,
            exc_info=e,
        )

    try:
        # Simulate a validation error
        raise ValueError("Invalid credit card number")
    except Exception as e:
        logger.warning(
            "Payment validation failed",
            error_type=type(e).__name__,
            error_message=str(e),
            user_notified=True,
            exc_info=e,
        )

    print("✅ Error handling completed!")


async def demonstrate_async_logging():
    """Demonstrate async logging patterns."""
    print("\n=== Async Logging ===")

    logger = micktrace.get_logger("async_demo").bind(
        service="async-processor", worker_id="worker_001"
    )

    async def process_item(item_id: int):
        """Process a single item asynchronously."""
        item_logger = logger.bind(item_id=f"item_{item_id:03d}")

        item_logger.info("Processing started")

        # Simulate async work
        processing_time = 0.1 + (item_id * 0.02)
        await asyncio.sleep(processing_time)

        item_logger.info(
            "Processing completed",
            duration_ms=round(processing_time * 1000, 2),
            status="success",
        )

        return f"processed_{item_id}"

    # Process multiple items concurrently
    logger.info("Starting async batch processing", batch_size=5)

    tasks = [process_item(i) for i in range(1, 6)]
    results = await asyncio.gather(*tasks)

    logger.info("Async batch completed",
                results_count=len(results), results=results)

    print("✅ Async logging completed!")


def demonstrate_performance_monitoring():
    """Demonstrate performance monitoring patterns."""
    print("\n=== Performance Monitoring ===")

    logger = micktrace.get_logger("perf_demo").bind(
        component="performance_monitor")

    # Simulate different operations with timing
    operations = [
        ("database_query", 0.05),
        ("api_call", 0.12),
        ("file_processing", 0.08),
        ("cache_lookup", 0.01),
    ]

    for operation_name, base_time in operations:
        start_time = time.time()

        # Simulate work
        actual_time = base_time + (
            base_time * 0.2 * (2 * hash(operation_name) % 100 - 50) / 100
        )
        time.sleep(max(0.01, actual_time))

        duration = time.time() - start_time
        duration_ms = round(duration * 1000, 2)

        # Log with performance context
        perf_logger = logger.bind(operation=operation_name)

        if duration_ms > 100:  # Slow operation
            perf_logger.warning(
                "Slow operation detected",
                duration_ms=duration_ms,
                threshold_ms=100,
                needs_optimization=True,
            )
        else:
            perf_logger.info(
                "Operation completed", duration_ms=duration_ms, performance="good"
            )

    print("✅ Performance monitoring completed!")


def demonstrate_file_logging():
    """Demonstrate file-only logging."""
    print("\n=== File Logging ===")

    # Configure file-only logging
    micktrace.configure(
        level="INFO",
        format="structured",
        handlers=[
            {
                "type": "file",
                "level": "INFO",
                "config": {"path": "logs/comprehensive_demo.log"},
            }
        ],
    )

    file_logger = micktrace.get_logger("file_demo").bind(
        component="file_processor", session_id=str(uuid4())
    )

    # Generate various log entries
    file_logger.info("File processing started", file_count=10)

    for i in range(5):
        file_logger.info(
            "Processing file",
            file_id=f"file_{i+1:03d}",
            file_size_bytes=1024 * (i + 1),
            progress_percent=((i + 1) / 5) * 100,
        )

    file_logger.info(
        "File processing completed",
        files_processed=5,
        total_size_bytes=1024 * 15,
        success_rate=100.0,
    )

    print("✅ File logging completed!")
    print("📄 Check logs/comprehensive_demo.log for file output")


def main():
    """Main function demonstrating all MickTrace features."""
    print("🚀 MickTrace Comprehensive Example")
    print("=" * 50)

    # Ensure logs directory exists
    import pathlib

    pathlib.Path("logs").mkdir(exist_ok=True)

    # Run all demonstrations
    demonstrate_basic_features()
    demonstrate_structured_logging()
    demonstrate_bound_loggers()
    demonstrate_error_handling()
    demonstrate_performance_monitoring()
    demonstrate_file_logging()

    # Run async demonstration
    asyncio.run(demonstrate_async_logging())

    print("\n🎉 All comprehensive examples completed successfully!")
    print("💡 MickTrace provides powerful, flexible logging for any application")


if __name__ == "__main__":
    main()
