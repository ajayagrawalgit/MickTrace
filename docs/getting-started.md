# Getting Started with Micktrace

Micktrace is the world's most advanced Python logging library, designed to be the de facto standard for all Python applications and libraries.

## Installation

```bash
pip install micktrace
```

## Quick Start

### For Libraries (Zero Configuration)

Libraries can start logging immediately with zero configuration:

```python
import micktrace

logger = micktrace.get_logger(__name__)
logger.info("Library initialized", version="1.0.0")
```

The logs are no-ops until the application configures micktrace.

### For Applications (Simple Configuration)

Applications activate logging with simple configuration:

```python
import micktrace

# Configure micktrace
micktrace.configure(level="INFO", format="json")

# Now all library logs will be output
logger = micktrace.get_logger(__name__)
logger.info("Application started", port=8080)
```

## Core Features

### Structured Logging by Default

Every log is automatically structured:

```python
logger.info("User logged in", 
           user_id=123, 
           username="alice", 
           ip_address="192.168.1.100",
           success=True)
```

### Async-Native Performance

Micktrace is built for async applications:

```python
import asyncio

async def main():
    async with micktrace.acontext(request_id="req_123"):
        logger.info("Processing async request")
        await process_data()

asyncio.run(main())
```

### Context Propagation

Automatic context injection across your application:

```python
with micktrace.context(user_id=123, session="sess_abc"):
    logger.info("User action")  # Automatically includes user_id and session
    call_other_functions()      # All nested logs include context
```

### High-Performance Timing

Built-in performance monitoring:

```python
with micktrace.timer("database_query") as timer:
    result = database.query("SELECT * FROM users")
    # Timing automatically logged
```

## Configuration

### Environment Variables

```bash
export MICKTRACE_LEVEL=INFO
export MICKTRACE_FORMAT=json
export MICKTRACE_HANDLERS=console,file
export MICKTRACE_FILE_PATH=/var/log/app.log
```

### Programmatic Configuration

```python
micktrace.configure({
    "level": "INFO",
    "format": "json",
    "handlers": [
        {
            "type": "console",
            "format": "rich",
            "level": "INFO"
        },
        {
            "type": "file",
            "path": "/var/log/app.log",
            "rotation": "daily",
            "compression": "gzip"
        }
    ],
    "context": {
        "service": "my-service",
        "version": "1.0.0"
    }
})
```

## Testing

Micktrace includes comprehensive testing utilities:

```python
import micktrace
from micktrace.testing import capture_logs

def test_my_function():
    with capture_logs() as logs:
        my_function()

    assert len(logs) == 1
    assert logs[0].level == "INFO"
    assert logs[0].message == "Function completed"
```

## Next Steps

- Read the [Full Documentation](https://micktrace.readthedocs.io)
- Check out [More Examples](examples/)
- Learn about [Performance Optimization](performance.md)
- Explore [Cloud Integration](cloud.md)
