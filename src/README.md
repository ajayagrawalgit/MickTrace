# MickTrace Source Code - Python Logging Library

This directory contains the source code for MickTrace, a modern Python logging library designed for production applications.

**Created by [Ajay Agrawal](https://github.com/ajayagrawalgit) | [LinkedIn](https://www.linkedin.com/in/theajayagrawal/)**
**Repository**: [https://github.com/ajayagrawalgit/MickTrace](https://github.com/ajayagrawalgit/MickTrace)

## 📁 Directory Structure

```
src/micktrace/
{{ ... }}
├── __init__.py          # Public API exports
├── types.py             # Core type definitions
├── core/                # Core logging engine
│   ├── __init__.py
│   ├── logger.py        # Main Logger class
│   └── context.py       # Context management
├── config/              # Configuration system
│   ├── __init__.py
│   └── configuration.py # Configuration management
├── handlers/            # Output destinations
│   ├── __init__.py
│   ├── handlers.py      # Base handler and FileHandler
│   ├── console.py       # Console, Null, Memory handlers
│   └── rotating.py      # Rotating file handler
├── formatters/          # Output formatters
│   ├── __init__.py
│   └── formatters.py    # JSON, structured formatters
└── filters/             # Log filtering
    ├── __init__.py
    └── filters.py       # Level, sampling filters
```

## 🧩 Module Overview

### `types.py`
Core type definitions used throughout MickTrace:
- `LogLevel`: Enum for log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LogRecord`: Dataclass representing a single log entry
- Type hints and protocols for extensibility

### `core/`
The heart of MickTrace's logging engine:

#### `logger.py`
- `Logger`: Main logger class with structured logging support
- `BoundLogger`: Logger with bound context data
- `get_logger()`: Factory function for creating loggers
- Thread-safe, async-compatible logging implementation

#### `context.py`
Context management for automatic data injection:
- `Context`: Context data container
- `ContextProvider`: Interface for context providers
- `get_context()`, `set_context()`: Context manipulation
- Async context propagation support

### `config/`
Configuration management system:

#### `configuration.py`
- `HandlerConfig`: Configuration for individual handlers
- `MickTraceConfig`: Main configuration class
- `configure()`: Global configuration function
- Environment variable support and validation
- Hot-reload capabilities

### `handlers/`
Output destinations for log records:

#### `handlers.py`
- `Handler`: Base handler class
- `FileHandler`: Write logs to files
- Level filtering and error handling

#### `console.py`
- `ConsoleHandler`: Write logs to console/terminal
- `NullHandler`: Discard logs (useful for testing)
- `MemoryHandler`: Store logs in memory (useful for testing)

#### `rotating.py`
- `RotatingFileHandler`: File handler with rotation support
- Size-based and time-based rotation
- Automatic cleanup of old log files

#### Cloud Platform Handlers (Optional Dependencies)
- `cloudwatch.py`: AWS CloudWatch Logs integration (`pip install micktrace[aws]`)
- `azure.py`: Azure Monitor integration (`pip install micktrace[azure]`)
- `stackdriver.py`: Google Cloud Logging (`pip install micktrace[gcp]`)
- `async_cloudwatch.py`: Async AWS CloudWatch handler
- `async_azure.py`: Async Azure Monitor handler
- `async_stackdriver.py`: Async Google Cloud handler

### `formatters/`
Log record formatting:

#### `formatters.py`
- `Formatter`: Base formatter class
- `JSONFormatter`: Output logs as JSON
- `StructuredFormatter`: Human-readable structured format
- `SimpleFormatter`: Basic text format
- Customizable field selection and formatting

### `filters/`
Log filtering and sampling:

#### `filters.py`
- `Filter`: Base filter class
- `LevelFilter`: Filter by log level
- `SamplingFilter`: Statistical sampling of logs
- `RateLimitFilter`: Rate limiting for high-volume scenarios

## 🔧 Key Design Principles

### 1. **Library-First Design**
- No global state pollution
- Libraries can log without configuration
- Applications control all output

### 2. **Error Resilience**
- Comprehensive try/catch blocks
- Graceful degradation on failures
- Never crash the host application

### 3. **Performance Optimized**
- Lazy evaluation of log messages
- Minimal overhead when logging disabled
- Efficient memory usage

### 4. **Type Safety**
- Full type hints throughout
- Structured data validation
- IDE-friendly development experience

### 5. **Extensibility**
- Plugin architecture for handlers
- Custom formatter support
- Filter chain composition

### 6. **Optional Dependencies Architecture**
- Minimal core with zero external dependencies
- Cloud integrations as optional extras
- Graceful degradation when dependencies missing
- Clear error messages for missing integrations

## 🔄 Data Flow

1. **Log Call**: `logger.info("message", key=value)`
2. **Level Check**: Verify if log should be processed
3. **Record Creation**: Create `LogRecord` with metadata
4. **Context Injection**: Add automatic context data
5. **Filter Chain**: Apply configured filters
6. **Handler Processing**: Send to configured handlers
7. **Formatting**: Format record for output
8. **Output**: Write to destination (file, console, etc.)

## 🧪 Testing Architecture

### Test Utilities
- `MemoryHandler`: Capture logs for assertions
- `NullHandler`: Discard logs during tests
- Context isolation for test independence

### Example Test Pattern
```python
import micktrace
from micktrace.handlers import MemoryHandler

def test_logging():
    handler = MemoryHandler()
    micktrace.configure(handlers=[handler])
    
    logger = micktrace.get_logger("test")
    logger.info("test message", key="value")
    
    records = handler.get_records()
    assert len(records) == 1
    assert records[0].data["key"] == "value"
```

## 🚀 Performance Considerations

### Hot Path Optimization
- Minimal allocations in logging calls
- Fast level checking
- Efficient context propagation

### Memory Management
- Automatic cleanup of old records
- Bounded memory usage in handlers
- Lazy string formatting

### Async Support
- Non-blocking I/O operations
- Context propagation across await boundaries
- Efficient batching for high throughput

## 🔌 Extension Points

### Custom Handlers
```python
from micktrace.handlers import Handler

class CustomHandler(Handler):
    def emit(self, record):
        # Custom output logic
        pass
```

### Custom Formatters
```python
from micktrace.formatters import Formatter

class CustomFormatter(Formatter):
    def format(self, record):
        # Custom formatting logic
        return formatted_string
```

### Custom Filters
```python
from micktrace.filters import Filter

class CustomFilter(Filter):
    def should_log(self, record):
        # Custom filtering logic
        return True
```

## 📊 Configuration Schema

### Handler Configuration
```python
{
    "type": "file",           # Handler type
    "level": "INFO",          # Minimum level
    "format": "json",         # Output format
    "enabled": True,          # Enable/disable
    "config": {               # Handler-specific config
        "path": "app.log",
        "rotation": "daily"
    }
}
```

### Global Configuration
```python
{
    "level": "INFO",          # Global level
    "format": "structured",   # Default format
    "enabled": True,          # Global enable/disable
    "service": "my-app",      # Service name
    "version": "1.0.0",       # Service version
    "environment": "prod",    # Environment
    "handlers": [...],        # Handler configurations
    "filters": [...]          # Filter configurations
}
```

## 📦 Optional Dependencies Pattern

### Graceful Degradation Example
```python
# In cloudwatch.py
try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None

class CloudWatchHandler:
    def __init__(self, ...):
        if boto3 is None:
            raise ImportError(
                "AWS CloudWatch integration requires additional dependencies. "
                "Install with: pip install micktrace[aws]"
            )
        # ... rest of initialization
```

### Installation Patterns
```bash
# Minimal installation
pip install micktrace

# Cloud platforms
pip install micktrace[aws]      # AWS CloudWatch, S3
pip install micktrace[azure]    # Azure Monitor
pip install micktrace[gcp]      # Google Cloud Logging

# Analytics platforms  
pip install micktrace[datadog]  # Datadog integration
pip install micktrace[elastic]  # Elasticsearch

# Performance enhancements
pip install micktrace[performance]  # orjson, lz4, msgpack

# Everything
pip install micktrace[all]
```

### Dependency Groups
- **Core**: `typing-extensions` (Python < 3.11 only)
- **AWS**: `aioboto3`, `botocore` 
- **Azure**: `azure-monitor-ingestion`, `azure-core`
- **GCP**: `google-cloud-logging`
- **Analytics**: `datadog`, `newrelic`, `elasticsearch`, `prometheus-client`, `sentry-sdk`
- **Performance**: `orjson`, `msgpack`, `lz4`
- **Rich**: `rich` (colored console output)
- **OpenTelemetry**: `opentelemetry-api`, `opentelemetry-sdk`

This architecture provides a solid foundation for production-grade logging while maintaining simplicity and performance.
