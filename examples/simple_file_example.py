"""
Simple File Logging Example - Production Ready
==============================================

This example shows basic file logging with MickTrace.
Perfect for production applications that need file-only logging.
"""

import micktrace
from pathlib import Path


def main():
    """Demonstrate simple file logging."""
    print("🚀 Simple File Logging Example")

    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure file-only logging
    micktrace.configure(
        level="INFO",
        format="structured",
        handlers=[
            {
                "type": "file",
                "level": "INFO",
                "config": {"path": "logs/simple_example.log"},
            }
        ],
    )

    # Get logger
    logger = micktrace.get_logger("simple_example")

    # Log some messages
    logger.info("Application started", version="1.0.0", environment="production")
    logger.info("Processing user request", user_id=12345, action="login")
    logger.warning("Rate limit approaching", current_requests=950, limit=1000)
    logger.error("Database connection failed", error_code="DB_001", retry_count=3)
    logger.info("Application shutdown", uptime_seconds=3600)

    print("✅ Logs written to logs/simple_example.log")
    print("🚫 No console output from logger (file-only)")


if __name__ == "__main__":
    main()
