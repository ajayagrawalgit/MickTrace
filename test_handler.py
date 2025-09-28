#!/usr/bin/env python3
"""Simple test to debug handler creation."""

import micktrace
from pathlib import Path

# Create logs directory
Path("logs").mkdir(exist_ok=True)

print("=== Testing MickTrace Handler Creation ===")

# Configure with file handler only
print("Configuring micktrace...")
micktrace.configure(
    enabled=True,
    level="INFO",
    handlers=[{
        "type": "file", 
        "level": "INFO",
        "config": {"path": "logs/test.log"}
    }]
)

print("Getting logger...")
logger = micktrace.get_logger("test")

print(f"Logger handlers: {logger._handlers}")
print(f"Number of handlers: {len(logger._handlers)}")

for i, handler in enumerate(logger._handlers):
    print(f"Handler {i}: {type(handler).__name__}")
    print(f"  - filename: {getattr(handler, 'filename', 'no filename')}")
    print(f"  - level: {getattr(handler, 'level', 'no level')}")
    print(f"  - all attributes: {[attr for attr in dir(handler) if not attr.startswith('_')]}")

# Also check configuration
config = micktrace.get_configuration()
print(f"Configuration handlers: {config.handlers}")
for i, hconfig in enumerate(config.handlers):
    print(f"Config handler {i}: type={hconfig.type}, config={hconfig.config}")

print("Logging test message...")
logger.info("This is a test message", data={"test": "value"})

print("Checking if log file exists...")
log_file = Path("logs/test.log")
if log_file.exists():
    print(f"✓ Log file created: {log_file}")
    print("Log file contents:")
    print(log_file.read_text())
else:
    print("✗ Log file not created")

print("=== Test Complete ===")
