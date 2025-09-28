#!/usr/bin/env python3
"""Test production-like configuration."""

import micktrace
from pathlib import Path

# Replicate production example setup
SERVICE_NAME = "MusicStream"
LOG_FILE = Path("logs") / "music_stream.log"

# Create log directory if it doesn't exist
LOG_FILE.parent.mkdir(exist_ok=True)

print("=== Testing Production Configuration ===")

# Disable first (like production example)
micktrace.disable()

# Configure once with only file handler (like production example)
print(f"Configuring with LOG_FILE: {LOG_FILE}")
micktrace.configure(
    enabled=True,
    level="INFO",
    format="structured",
    service=SERVICE_NAME,
    handlers=[{
        "type": "file", 
        "level": "INFO",
        "config": {"path": str(LOG_FILE)}
    }]
)

# Create the logger AFTER configuration - it will use the configured handlers
logger = micktrace.get_logger(SERVICE_NAME)

print(f"Logger handlers: {len(logger._handlers)}")
for i, handler in enumerate(logger._handlers):
    print(f"Handler {i}: {type(handler).__name__} - {getattr(handler, 'filename', 'no filename')}")

print("Logging test message...")
logger.info("Music streaming service starting", data={
    "service": SERVICE_NAME,
    "log_file": str(LOG_FILE),
    "test": True
})

print("Checking if log file exists...")
if LOG_FILE.exists():
    print(f"✓ Log file created: {LOG_FILE}")
    print("Log file contents:")
    print(LOG_FILE.read_text())
else:
    print("✗ Log file not created")

print("=== Test Complete ===")
