# API Reference

## Core Functions

### `micktrace.get_logger(name=None)`

Get a logger instance.

**Parameters:**
- `name` (str, optional): Logger name. Defaults to caller's module name.

**Returns:**
- `Logger`: Logger instance

**Example:**
```python
logger = micktrace.get_logger(__name__)
```

### `micktrace.configure(**kwargs)`

Configure micktrace programmatically.

**Parameters:**
- `level` (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `format` (str): Output format (json, logfmt, structured, rich, simple)
- `handlers` (list): List of handler configurations
- `context` (dict): Global context data

**Example:**
```python
micktrace.configure(level="INFO", format="json", handlers=["console"])
```

## Logger Class

### `Logger.info(message, **kwargs)`

Log an INFO level message.

**Parameters:**
- `message` (str): Log message
- `**kwargs`: Additional structured data

**Example:**
```python
logger.info("User action", user_id=123, action="login")
```

### `Logger.debug(message, **kwargs)`

Log a DEBUG level message.

### `Logger.warning(message, **kwargs)`

Log a WARNING level message.

### `Logger.error(message, **kwargs)`

Log an ERROR level message.

### `Logger.critical(message, **kwargs)`

Log a CRITICAL level message.

### `Logger.exception(message, **kwargs)`

Log an ERROR level message with exception info.

### `Logger.bind(**kwargs)`

Create a bound logger with additional context.

**Returns:**
- `BoundLogger`: Logger with bound context

**Example:**
```python
service_logger = logger.bind(service="auth", version="1.0")
service_logger.info("Service started")  # Includes service and version
```

## Context Management

### `micktrace.context(**kwargs)`

Context manager for temporary context data.

**Example:**
```python
with micktrace.context(user_id=123, request_id="req_456"):
    logger.info("Request processed")  # Includes user_id and request_id
```

### `micktrace.acontext(**kwargs)`

Async context manager for temporary context data.

### `micktrace.get_context()`

Get current context data.

**Returns:**
- `dict`: Current context

### `micktrace.set_context(**kwargs)`

Set context data.

## Tracing and Timing

### `micktrace.timer(name=None, **metadata)`

Context manager for timing operations.

**Example:**
```python
with micktrace.timer("database_query") as timer:
    result = db.query("SELECT * FROM users")
    # Timing automatically logged
```

### `micktrace.trace(name, **metadata)`

Context manager for distributed tracing.

**Example:**
```python
with micktrace.trace("request_processing") as tracer:
    span_id = tracer.start_span("auth")
    authenticate_user()
    tracer.end_span(span_id)
```

### `micktrace.now()`

Get current high-precision timestamp.

**Returns:**
- `float`: Current timestamp

### `micktrace.elapsed(start_time)`

Calculate elapsed time from start timestamp.

**Parameters:**
- `start_time` (float): Start timestamp from `now()`

**Returns:**
- `float`: Elapsed time in seconds

## Testing Utilities

### `micktrace.testing.capture_logs(logger_name=None, level="DEBUG")`

Context manager for capturing logs during tests.

**Example:**
```python
from micktrace.testing import capture_logs

with capture_logs() as logs:
    logger.info("Test message")

assert len(logs) == 1
assert logs[0].message == "Test message"
```

### `LogCapture.assert_logged(level, message=None, **data)`

Assert that a log record was captured.

**Parameters:**
- `level` (str): Expected log level
- `message` (str, optional): Expected message content
- `**data`: Expected structured data

**Returns:**
- `bool`: True if matching record found

## Handler Classes

### `ConsoleHandler`

Output logs to console with rich formatting.

### `FileHandler`

Output logs to files with rotation and compression.

### `HTTPHandler`

Send logs to HTTP endpoints with batching and retries.

### `MemoryHandler`

Store logs in memory for testing.

## Configuration Classes

### `Configuration`

Main configuration class with validation.

### `HandlerConfig`

Configuration for individual handlers.

### `ContextConfig`

Configuration for automatic context injection.
