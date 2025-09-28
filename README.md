# MickTrace - Python Logging Library

[![Python Version](https://img.shields.io/pypi/pyversions/micktrace.svg)](https://pypi.org/project/micktrace/)
[![PyPI Version](https://img.shields.io/pypi/v/micktrace.svg)](https://pypi.org/project/micktrace/)
[![License](https://img.shields.io/pypi/l/micktrace.svg)](https://github.com/ajayagrawalgit/MickTrace/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/micktrace.svg)](https://pypi.org/project/micktrace/)
[![GitHub Stars](https://img.shields.io/github/stars/ajayagrawalgit/MickTrace.svg)](https://github.com/ajayagrawalgit/MickTrace)

**Modern Python logging library designed for production applications and libraries.** Built with async-first architecture, structured logging, and zero-configuration philosophy.

**Created by [Ajay Agrawal](https://github.com/ajayagrawalgit) | [LinkedIn](https://www.linkedin.com/in/theajayagrawal/)**

---

## 🚀 Why Choose MickTrace?

### **For Production Applications**
- **Zero Configuration Required** - Works out of the box, configure when needed
- **Async-Native Performance** - Sub-microsecond overhead when logging disabled
- **Structured by Default** - JSON, logfmt, and custom formats built-in
- **Cloud-Ready** - Native AWS, Azure, GCP integrations with graceful fallbacks
- **Memory Safe** - No memory leaks, proper cleanup, production-tested

### **For Library Developers**
- **Library-First Design** - No global state pollution, safe for libraries
- **Zero Dependencies** - Core functionality requires no external packages
- **Type Safety** - Full type hints, mypy compatible, excellent IDE support
- **Backwards Compatible** - Drop-in replacement for standard logging

### **For Development Teams**
- **Context Propagation** - Automatic request/trace context across async boundaries
- **Hot Reloading** - Change log levels and formats without restart
- **Rich Console Output** - Beautiful, readable logs during development
- **Comprehensive Testing** - 200+ tests ensure reliability

---

## 📦 Installation

### Basic Installation
```bash
pip install micktrace
```

### Cloud Platform Integration
```bash
# AWS CloudWatch
pip install micktrace[aws]

# Azure Monitor  
pip install micktrace[azure]

# Google Cloud Logging
pip install micktrace[gcp]

# All cloud platforms
pip install micktrace[cloud]
```

### Analytics & Monitoring
```bash
# Datadog integration
pip install micktrace[datadog]

# New Relic integration
pip install micktrace[newrelic]

# Elastic Stack integration
pip install micktrace[elastic]

# All analytics tools
pip install micktrace[analytics]
```

### Development & Performance
```bash
# Rich console output
pip install micktrace[rich]

# Performance monitoring
pip install micktrace[performance]

# OpenTelemetry integration
pip install micktrace[opentelemetry]

# Everything included
pip install micktrace[all]
```

---

## ⚡ Quick Start

### **Instant Logging (Zero Config)**
```python
import micktrace

logger = micktrace.get_logger(__name__)
logger.info("Application started", version="1.0.0", env="production")
```

### **Structured Logging**
```python
import micktrace

logger = micktrace.get_logger("api")

# Automatic structured output
logger.info("User login", 
           user_id=12345, 
           email="user@example.com",
           ip_address="192.168.1.1",
           success=True)
```

### **Async Context Propagation**
```python
import asyncio
import micktrace

async def handle_request():
    async with micktrace.acontext(request_id="req_123", user_id=456):
        logger = micktrace.get_logger("handler")
        logger.info("Processing request")
        
        await process_data()  # Context automatically propagated
        
        logger.info("Request completed")

async def process_data():
    logger = micktrace.get_logger("processor")
    logger.info("Processing data")  # Includes request_id and user_id automatically
```

### **Application Configuration**
```python
import micktrace

# Configure for your application
micktrace.configure(
    level="INFO",
    format="json",
    service="my-app",
    version="1.0.0",
    environment="production",
    handlers=[
        {"type": "console"},
        {"type": "file", "config": {"path": "app.log"}},
        {"type": "cloudwatch", "config": {"log_group": "my-app"}}
    ]
)
```

---

## 🌟 Key Features

### **🔥 Performance Optimized**
- **Sub-microsecond overhead** when logging disabled
- **Async-native architecture** - no blocking operations
- **Memory efficient** - automatic cleanup and bounded memory usage
- **Hot-path optimized** - critical paths designed for speed

### **🏗️ Production Ready**
- **Zero global state** - safe for libraries and applications
- **Graceful degradation** - continues working even when components fail
- **Thread and async safe** - proper synchronization throughout
- **Comprehensive error handling** - never crashes your application

### **📊 Structured Logging**
- **JSON output** - machine-readable logs for analysis
- **Logfmt support** - human-readable structured format
- **Custom formatters** - extend with your own formats
- **Automatic serialization** - handles complex Python objects

### **🌐 Cloud Native**
- **AWS CloudWatch** - native integration with batching and retry
- **Azure Monitor** - structured logging to Azure
- **Google Cloud Logging** - GCP-native structured logs
- **Kubernetes ready** - proper JSON output for container environments

### **🔄 Context Management**
- **Request tracing** - automatic correlation IDs
- **Async propagation** - context flows across await boundaries
- **Bound loggers** - attach permanent context to loggers
- **Dynamic context** - runtime context injection

### **⚙️ Developer Experience**
- **Zero configuration** - works immediately out of the box
- **Hot reloading** - change configuration without restart
- **Rich console** - beautiful development output
- **Full type hints** - excellent IDE support and error detection

---

## 🏢 Cloud Platform Integration

### **AWS CloudWatch**
```python
import micktrace

micktrace.configure(
    level="INFO",
    handlers=[{
        "type": "cloudwatch",
        "log_group_name": "my-application",
        "log_stream_name": "production",
        "region": "us-east-1"
    }]
)

logger = micktrace.get_logger(__name__)
logger.info("Lambda function executed", duration_ms=150, memory_used=64)
```

### **Azure Monitor**
```python
import micktrace

micktrace.configure(
    level="INFO", 
    handlers=[{
        "type": "azure",
        "connection_string": "InstrumentationKey=your-key"
    }]
)

logger = micktrace.get_logger(__name__)
logger.info("Azure function completed", execution_time=200)
```

### **Google Cloud Logging**
```python
import micktrace

micktrace.configure(
    level="INFO",
    handlers=[{
        "type": "stackdriver",
        "project_id": "my-gcp-project",
        "log_name": "my-app-log"
    }]
)

logger = micktrace.get_logger(__name__)
logger.info("GCP service call", service="storage", operation="upload")
```

### **Multi-Platform Setup**
```python
import micktrace

micktrace.configure(
    level="INFO",
    handlers=[
        {"type": "console"},  # Development
        {"type": "cloudwatch", "config": {"log_group": "prod-logs"}},  # AWS
        {"type": "azure", "config": {"connection_string": "..."}},     # Azure
        {"type": "file", "config": {"path": "/var/log/app.log"}}       # Local
    ]
)
```

---

## 📈 Analytics & Monitoring Integration

### **Datadog Integration**
```python
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
logger.info("Payment processed", amount=100.0, currency="USD", customer_id=12345)
```

### **New Relic Integration**
```python
import micktrace

micktrace.configure(
    level="INFO",
    handlers=[{
        "type": "newrelic",
        "license_key": "your-license-key",
        "app_name": "my-application"
    }]
)

logger = micktrace.get_logger(__name__)
logger.info("Database query", table="users", duration_ms=45, rows_returned=150)
```

### **Elastic Stack Integration**
```python
import micktrace

micktrace.configure(
    level="INFO",
    handlers=[{
        "type": "elasticsearch",
        "hosts": ["localhost:9200"],
        "index": "application-logs"
    }]
)

logger = micktrace.get_logger(__name__)
logger.info("Search query", query="python logging", results=1250, response_time_ms=23)
```

---

## 🎯 Use Cases

### **Web Applications**
```python
import micktrace
from flask import Flask, request

app = Flask(__name__)

# Configure structured logging
micktrace.configure(
    level="INFO",
    format="json",
    service="web-api",
    handlers=[{"type": "console"}, {"type": "file", "config": {"path": "api.log"}}]
)

@app.route("/api/users", methods=["POST"])
def create_user():
    with micktrace.context(
        request_id=request.headers.get("X-Request-ID"),
        endpoint="/api/users",
        method="POST"
    ):
        logger = micktrace.get_logger("api")
        logger.info("User creation started")
        
        # Your business logic here
        user_id = create_user_in_db()
        
        logger.info("User created successfully", user_id=user_id)
        return {"user_id": user_id}
```

### **Microservices**
```python
import micktrace
import asyncio

# Service A
async def service_a_handler(trace_id: str):
    async with micktrace.acontext(trace_id=trace_id, service="service-a"):
        logger = micktrace.get_logger("service-a")
        logger.info("Processing request in service A")
        
        # Call service B
        result = await call_service_b(trace_id)
        
        logger.info("Service A completed", result=result)
        return result

# Service B  
async def service_b_handler(trace_id: str):
    async with micktrace.acontext(trace_id=trace_id, service="service-b"):
        logger = micktrace.get_logger("service-b")
        logger.info("Processing request in service B")
        
        # Business logic
        await process_data()
        
        logger.info("Service B completed")
        return "success"
```

### **Data Processing**
```python
import micktrace

logger = micktrace.get_logger("data-processor")

def process_batch(batch_id: str, items: list):
    with micktrace.context(batch_id=batch_id, batch_size=len(items)):
        logger.info("Batch processing started")
        
        processed = 0
        failed = 0
        
        for item in items:
            item_logger = logger.bind(item_id=item["id"])
            try:
                process_item(item)
                item_logger.info("Item processed successfully")
                processed += 1
            except Exception as e:
                item_logger.error("Item processing failed", error=str(e))
                failed += 1
        
        logger.info("Batch processing completed", 
                   processed=processed, 
                   failed=failed,
                   success_rate=processed/len(items))
```

### **Library Development**
```python
# Your library code
import micktrace

class MyLibrary:
    def __init__(self):
        # Library gets its own logger - no global state pollution
        self.logger = micktrace.get_logger("my_library")
    
    def process_data(self, data):
        self.logger.debug("Processing data", data_size=len(data))
        
        # Your processing logic
        result = self._internal_process(data)
        
        self.logger.info("Data processed successfully", 
                        input_size=len(data),
                        output_size=len(result))
        return result
    
    def _internal_process(self, data):
        # Library logging works regardless of application configuration
        self.logger.debug("Internal processing step")
        return data.upper()

# Application using your library
import micktrace
from my_library import MyLibrary

# Application configures logging
micktrace.configure(level="INFO", format="json")

# Library logging automatically follows application configuration
lib = MyLibrary()
result = lib.process_data("hello world")
```

---

## 🔧 Advanced Configuration

### **Environment-Based Configuration**
```python
import os
import micktrace

# Automatic environment variable support
os.environ["MICKTRACE_LEVEL"] = "DEBUG"
os.environ["MICKTRACE_FORMAT"] = "json"

# Configuration picks up environment variables automatically
micktrace.configure(
    service=os.getenv("SERVICE_NAME", "my-app"),
    environment=os.getenv("ENVIRONMENT", "development")
)
```

### **Dynamic Configuration**
```python
import micktrace

# Hot-reload configuration without restart
def update_log_level(new_level: str):
    micktrace.configure(level=new_level)
    logger = micktrace.get_logger("config")
    logger.info("Log level updated", new_level=new_level)

# Change configuration at runtime
update_log_level("DEBUG")  # Now debug logs will appear
update_log_level("ERROR")  # Now only errors will appear
```

### **Custom Formatters**
```python
import micktrace
from micktrace.formatters import Formatter

class CustomFormatter(Formatter):
    def format(self, record):
        return f"[{record.level.name}] {record.timestamp} | {record.message} | {record.data}"

micktrace.configure(
    level="INFO",
    handlers=[{
        "type": "console",
        "formatter": CustomFormatter()
    }]
)
```

### **Filtering and Sampling**
```python
import micktrace

# Sample only 10% of debug logs to reduce volume
micktrace.configure(
    level="DEBUG",
    handlers=[{
        "type": "console",
        "filters": [
            {"type": "level", "level": "INFO"},  # Only INFO and above
            {"type": "sample", "rate": 0.1}     # Sample 10% of logs
        ]
    }]
)
```

---

## 🧪 Testing and Development

### **Testing Support**
```python
import micktrace
import pytest

def test_my_function():
    # Capture logs during testing
    with micktrace.testing.capture_logs() as captured:
        my_function_that_logs()
        
        # Assert log content
        assert len(captured.records) == 2
        assert captured.records[0].message == "Function started"
        assert captured.records[1].level == micktrace.LogLevel.INFO

def test_with_context():
    # Test context propagation
    with micktrace.context(test_id="test_123"):
        logger = micktrace.get_logger("test")
        logger.info("Test message")
        
        # Context is available
        ctx = micktrace.get_context()
        assert ctx["test_id"] == "test_123"
```

### **Development Configuration**
```python
import micktrace

# Rich console output for development
micktrace.configure(
    level="DEBUG",
    format="rich",  # Beautiful console output
    handlers=[{
        "type": "rich_console",
        "show_time": True,
        "show_level": True,
        "show_path": True
    }]
)
```

---

## 📊 Performance Characteristics

### **Benchmarks**
- **Disabled logging**: < 50 nanoseconds overhead
- **Structured logging**: ~2-5 microseconds per log
- **Context operations**: ~100 nanoseconds per context access
- **Async context propagation**: Zero additional overhead
- **Memory usage**: Bounded, automatic cleanup

### **Scalability**
- **High throughput**: 100,000+ logs/second per thread
- **Low latency**: Sub-millisecond 99th percentile
- **Memory efficient**: Constant memory usage under load
- **Async optimized**: No blocking operations in hot paths

### **Production Tested**
- **Zero memory leaks** - extensive testing with long-running applications
- **Thread safety** - safe for multi-threaded applications
- **Async safety** - proper context isolation in concurrent operations
- **Error resilience** - continues working even when components fail

---

## 🤝 Contributing

MickTrace welcomes contributions! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

### **Quick Start for Contributors**
```bash
# Clone the repository
git clone https://github.com/ajayagrawalgit/MickTrace.git
cd MickTrace

# Install development dependencies
pip install -e .[dev]

# Run tests
pytest tests/ -v

# Run performance tests
pytest tests/test_performance.py -v
```

### **Development Setup**
```bash
# Install all optional dependencies for testing
pip install -e .[all]

# Run comprehensive tests
pytest tests/ --cov=micktrace

# Check code quality
black src/ tests/
mypy src/
ruff check src/ tests/
```

### **Test Suite**
- **200+ comprehensive tests** covering all functionality
- **Performance benchmarks** for critical paths
- **Integration tests** for real-world scenarios
- **Async tests** for context propagation
- **Error handling tests** for resilience

See [tests/README.md](tests/README.md) for detailed testing documentation.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

**Copyright (c) 2025 [Ajay Agrawal](https://github.com/ajayagrawalgit)**

---

## 🔗 Links

- **Repository**: [https://github.com/ajayagrawalgit/MickTrace](https://github.com/ajayagrawalgit/MickTrace)
- **PyPI Package**: [https://pypi.org/project/micktrace/](https://pypi.org/project/micktrace/)
- **Author**: [Ajay Agrawal](https://github.com/ajayagrawalgit)
- **LinkedIn**: [https://www.linkedin.com/in/theajayagrawal/](https://www.linkedin.com/in/theajayagrawal/)
- **Issues**: [https://github.com/ajayagrawalgit/MickTrace/issues](https://github.com/ajayagrawalgit/MickTrace/issues)

---

## 🏷️ Keywords

`python logging` • `async logging` • `structured logging` • `json logging` • `cloud logging` • `aws cloudwatch` • `azure monitor` • `google cloud logging` • `datadog logging` • `observability` • `tracing` • `monitoring` • `performance logging` • `production logging` • `library logging` • `context propagation` • `correlation id` • `microservices logging` • `kubernetes logging` • `docker logging` • `elasticsearch logging` • `logfmt` • `python logger` • `async python` • `logging library` • `log management` • `application logging` • `system logging` • `enterprise logging`

---

**Built with ❤️ by [Ajay Agrawal](https://github.com/ajayagrawalgit) for the Python community**
