#!/usr/bin/env python3
"""
Basic Micktrace Example - Demonstrates core features with error handling
"""

import sys
import os
from pathlib import Path
import asyncio

# Add src to path for running from source
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import micktrace
    from micktrace.types import LogLevel
except ImportError as e:
    print(f"Failed to import micktrace: {e}")
    sys.exit(1)


async def demonstrate_basic_logging():
    """Demonstrate basic logging features."""
    print("=== Basic Logging Demo ===")

    # Get a logger with DEBUG level
    logger = micktrace.get_logger(__name__, level=LogLevel.DEBUG)

    # Add console handler
    logger.add_handler("console")

    # Set correlation and trace IDs for distributed tracing
    logger.set_correlation_id("demo_correlation_id")
    logger.set_trace_id("demo_trace_id")

    # Basic logging with structured data
    logger.info("Application starting", data={"component": "main", "version": "1.0.0"})

    # Log with structured data
    logger.info("User logged in", data={
        "user_id": 123,
        "username": "alice",
        "ip_address": "192.168.1.100",
        "success": True
    })

    # Different log levels with rich data
    logger.debug("Debug information", data={"details": "only visible in debug"})
    logger.warning("Something suspicious", data={"threat_level": "low", "action_required": True})
    
    # Error logging with exception
    try:
        raise ValueError("Database connection failed")
    except Exception as e:
        logger.error("An error occurred", 
                    data={"error_code": 500, "retryable": True},
                    exc_info=e)

    # Async logging
    await logger.async_info("Async operation completed", 
                          data={"duration": 1.23, "status": "success"})

    print("✅ Basic logging completed successfully!")


async def demonstrate_context():
    """Demonstrate context and trace propagation."""
    logger = micktrace.get_logger("demo.context")

    print("=== Context and Tracing Demo ===")

    # Set trace context for distributed tracing
    logger.set_correlation_id("service_call_123")
    logger.set_trace_id("distributed_trace_abc")

    # Log service operations with tracing
    await logger.async_info("Processing request", 
                          data={"operation": "get_user_profile", "request_id": "req_12345"})
    
    await logger.async_info("Database query executed", 
                          data={"table": "users", "duration_ms": 45, "query_id": "q_789"})

    logger.info("Request processed successfully", 
               data={"status_code": 200, "response_time_ms": 123})

    print("✅ Context and tracing demo completed successfully!")


def main():
    """Main function demonstrating micktrace capabilities."""
    print("🚀 Micktrace Basic Example - Comprehensive Demo")
    print("=" * 60)

    try:
        asyncio.run(demonstrate_basic_logging())
        print()
        asyncio.run(demonstrate_context())
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
