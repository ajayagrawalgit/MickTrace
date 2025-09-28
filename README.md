# Micktrace 🚀

**The world's most advanced Python logging library - Zero shortcomings, perfect design**

[![Python](https://img.shields.io/pypi/pyversions/micktrace.svg)](https://pypi.org/project/micktrace/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Why Micktrace?

**🔥 Zero Configuration for Libraries** - Libraries can log immediately without any setup. Only applications control logging output.

**⚡ Async-Native Performance** - Sub-microsecond overhead when disabled, non-blocking I/O, built-in async support.

**📊 Structured by Default** - Every log is structured with type safety and automatic context injection.

**🏗️ Library-First Design** - No global state pollution. Multiple libraries can use Micktrace without conflicts.

**🚀 Future-Proof Architecture** - Built for modern Python with full type hints and comprehensive error handling.

## 🚀 Quick Start

```python
import micktrace

# For libraries - zero config needed, works immediately  
logger = micktrace.get_logger(__name__)
logger.info("Library initialized", component="auth", version="1.2.3")

# For applications - simple activation
micktrace.configure(level="INFO", format="structured")
```

## 📦 Installation

### Basic Installation
```bash
pip install micktrace
```
**Minimal dependencies** - Only `typing-extensions` for Python < 3.11

### Cloud Platform Integration
```bash
# AWS CloudWatch, S3, Kinesis
pip install micktrace[aws]

# Azure Monitor, Application Insights  
pip install micktrace[azure]

# Google Cloud Logging, BigQuery
pip install micktrace[gcp]

# All cloud platforms
pip install micktrace[cloud]
```

### Analytics & Monitoring Platforms
```bash
# Datadog integration
pip install micktrace[datadog]

# New Relic integration  
pip install micktrace[newrelic]

# Elasticsearch integration
pip install micktrace[elastic]

# Prometheus metrics
pip install micktrace[prometheus]

# Sentry error tracking
pip install micktrace[sentry]

# All analytics platforms
pip install micktrace[analytics]
```

### Performance & Features
```bash
# High-performance JSON/compression
pip install micktrace[performance]

# Rich console output with colors
pip install micktrace[rich]

# OpenTelemetry integration
pip install micktrace[opentelemetry]

# Everything (all integrations)
pip install micktrace[all]
```

### Mix & Match
```bash
# Custom combinations
pip install micktrace[aws,datadog,performance]
pip install micktrace[gcp,elastic,rich]
```

## ✨ Key Features

### 🔥 Performance First
- **Sub-microsecond overhead** when logging is disabled
- **Async-native** with automatic context propagation
- **Memory efficient** with intelligent batching
### Context Management
```python
# Add context to all logs in a scope
with micktrace.context(request_id="req_123", user_id=456):
    logger.info("Processing request")  # Includes request_id and user_id
    await process_data()  # All nested logs include context
```
```python
import micktrace

logger = micktrace.get_logger(__name__)

# Create bound logger with common context
service_logger = logger.bind(service="auth", version="1.0.0")
service_logger.info("Service started", port=8080)  # Includes service and version

# Chain binding for more specific context
request_logger = service_logger.bind(request_id="req_456")
request_logger.info("User authenticated")  # Includes service, version, and request_id
```

### Library Integration
```python
# In your library code - works immediately, zero setup
import micktrace

logger = micktrace.get_logger(__name__)

def library_function():
    logger.info("Library function called", function="library_function")
    # Logs are only emitted if the application configures micktrace
    # Otherwise, zero overhead
```

## 🧪 Testing Support

```python
import micktrace
from micktrace.handlers import MemoryHandler

def test_my_function():
    handler = MemoryHandler()
    # Configure micktrace to use memory handler for testing

    my_function()

    # Assert on logged records
    records = handler.get_records()
    assert len(records) == 1
    assert records[0].level == "INFO"
    assert records[0].data["user_id"] == 123
```

## 🎨 Advanced Features

### Exception Logging
```python
try:
    risky_operation()
except Exception:
    logger.exception("Operation failed", 
                    operation="risky_operation",
                    retry_count=3,
                    will_retry=True)
```

### Performance Monitoring
```python
import time
import micktrace

logger = micktrace.get_logger(__name__)

start_time = time.time()
try:
    result = expensive_operation()
    logger.info("Operation completed",
                operation="expensive_operation", 
                duration_ms=int((time.time() - start_time) * 1000),
                result_size=len(result))
except Exception as e:
    logger.error("Operation failed",
                operation="expensive_operation",
                duration_ms=int((time.time() - start_time) * 1000),
                error_type=type(e).__name__)
```

### Configuration Options
```python
# Environment-based configuration
import os
os.environ["MICKTRACE_LEVEL"] = "INFO"
os.environ["MICKTRACE_FORMAT"] = "json"
os.environ["MICKTRACE_HANDLERS"] = "console,file"

# Programmatic configuration
micktrace.configure(
    level="INFO",
    format="structured",  # json, logfmt, structured, simple
    handlers=["console"],
    service="my-service",
    version="1.0.0",
    environment="production"
)
```

## 📚 Output Formats

### Structured (Default)
```
2023-09-26 10:15:30 [    INFO] my_app: User logged in user_id=123 action=login success=True
```

### JSON
```json
{"timestamp": 1695720930.123, "level": "INFO", "logger_name": "my_app", "message": "User logged in", "data": {"user_id": 123, "action": "login", "success": true}, "trace_id": "550e8400-e29b-41d4-a716-446655440000"}
```

### Logfmt
```
timestamp=1695720930.123 level=INFO logger=my_app message="User logged in" user_id=123 action=login success=true trace_id=550e8400-e29b-41d4-a716-446655440000
```

## ☁️ Cloud Platform Integration

### AWS CloudWatch
```python
# pip install micktrace[aws]
import micktrace

micktrace.configure(
    level="INFO",
    handlers=[{
        "type": "cloudwatch",
        "log_group": "/aws/lambda/my-function",
        "log_stream": "my-stream",
        "region": "us-east-1"
    }]
)

logger = micktrace.get_logger(__name__)
logger.info("Lambda function executed", duration_ms=150, memory_used_mb=128)
```

### Azure Monitor
```python
# pip install micktrace[azure]
import micktrace

micktrace.configure(
    level="INFO", 
    handlers=[{
        "type": "azure",
        "workspace_id": "your-workspace-id",
        "shared_key": "your-shared-key",
        "log_type": "MyAppLogs"
    }]
)

logger = micktrace.get_logger(__name__)
logger.info("Application event", event_type="user_action", user_id=123)
```

### Google Cloud Logging
```python
# pip install micktrace[gcp]
import micktrace

micktrace.configure(
    level="INFO",
    handlers=[{
        "type": "stackdriver", 
        "project_id": "my-project",
        "log_name": "my-app-log"
    }]
)

logger = micktrace.get_logger(__name__)
logger.info("GCP service call", service="storage", operation="upload")
```

### Datadog Integration
```python
# pip install micktrace[datadog]
import micktrace

micktrace.configure(
    level="INFO",
    handlers=[{
        "type": "datadog",
        "api_key": "your-api-key", 
        "service": "my-service",
        "env": "production"
    }]
)

logger = micktrace.get_logger(__name__)
logger.info("Request processed", endpoint="/api/users", response_time_ms=45)
```

### Multi-Platform Setup
```python
# pip install micktrace[aws,datadog,elastic]
import micktrace

micktrace.configure(
    level="INFO",
    handlers=[
        {"type": "console"},  # Local development
        {"type": "cloudwatch", "log_group": "/aws/my-app"},  # AWS
        {"type": "datadog", "service": "my-app"},  # Monitoring
        {"type": "elasticsearch", "index": "logs-2024"}  # Search
    ]
)

# All handlers receive the same structured logs
logger = micktrace.get_logger(__name__)
logger.info("Multi-platform logging", user_id=123, action="login")
```

## 🏆 Why Better Than Alternatives

| Feature | stdlib logging | loguru | structlog | micktrace |
|---------|---------------|--------|-----------|-----------|
| Library-friendly | ❌ | ❌ | ⚠️ | ✅ |
| Zero config | ❌ | ✅ | ❌ | ✅ |
| Structured logging | ❌ | ⚠️ | ✅ | ✅ |
| Type safety | ❌ | ❌ | ⚠️ | ✅ |
| Async native | ❌ | ❌ | ❌ | ✅ |
| Context propagation | ❌ | ❌ | ✅ | ✅ |
| Testing utilities | ❌ | ❌ | ❌ | ✅ |
| Error handling | ⚠️ | ✅ | ⚠️ | ✅ |
| Performance | ⚠️ | ✅ | ⚠️ | ✅ |

## 🔧 Configuration Reference

### Environment Variables
- `MICKTRACE_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `MICKTRACE_FORMAT`: Output format (json, logfmt, structured, simple)
- `MICKTRACE_ENABLED`: Enable/disable logging (true/false)
- `MICKTRACE_HANDLERS`: Comma-separated list of handlers
- `MICKTRACE_SERVICE`: Service name for all logs
- `MICKTRACE_VERSION`: Service version for all logs
- `MICKTRACE_ENVIRONMENT`: Environment name (dev, staging, prod)

### Programmatic Configuration
```python
micktrace.configure(
    level="INFO",              # Minimum log level
    format="json",             # Output format
    enabled=True,              # Enable/disable logging
    handlers=["console"],      # List of handlers
    service="my-service",      # Service name
    version="1.0.0",          # Service version
    environment="production"   # Environment name
)
```

## 🤝 Contributing

Contributions welcome! This library aims to solve all Python logging problems once and for all.

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Run the test suite: `python tests/test_basic.py`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

Built with ❤️ for the Python community. Inspired by the best features of existing logging libraries while solving their fundamental limitations.

---

**Made with ❤️ by [Ajay Agrawal](mailto:ajay@micktrace.dev)**
