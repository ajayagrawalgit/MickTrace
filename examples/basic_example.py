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

    # Configure micktrace first
    micktrace.configure(
        level="DEBUG",
        format="structured",
        handlers=[{"type": "console"}]
    )

    # Get a logger
    logger = micktrace.get_logger(__name__)

    # Basic logging with structured data
    logger.info("Application starting", component="main", version="1.0.0")

    # Log with structured data
    logger.info("User logged in", 
                user_id=123,
                username="alice",
                ip_address="192.168.1.100",
                success=True)

    # Different log levels with rich data
    logger.debug("Debug information", details="only visible in debug")
    logger.warning("Something suspicious", threat_level="low", action_required=True)
    
    # Error logging with exception
    try:
        raise ValueError("Database connection failed")
    except Exception as e:
        logger.error("An error occurred", 
                    error_code=500, 
                    retryable=True,
                    exc_info=e)

    # Regular logging (async logging not available in current API)
    logger.info("Operation completed", duration=1.23, status="success")

    print("✅ Basic logging completed successfully!")


async def demonstrate_context():
    """Demonstrate context and bound loggers."""
    logger = micktrace.get_logger("demo.context")

    print("=== Context and Bound Logger Demo ===")

    # Create bound logger with context
    request_logger = logger.bind(
        request_id="req_12345",
        operation="get_user_profile"
    )

    # Log service operations with automatic context
    request_logger.info("Processing request")
    
    request_logger.info("Database query executed", 
                       table="users", 
                       duration_ms=45, 
                       query_id="q_789")

    request_logger.info("Request processed successfully", 
                       status_code=200, 
                       response_time_ms=123)

    print("✅ Context and bound logger demo completed successfully!")


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
