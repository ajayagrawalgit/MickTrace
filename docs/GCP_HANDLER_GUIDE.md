# Google Cloud Platform (GCP) Handler Guide

## Overview

MickTrace provides native integration with Google Cloud Logging (formerly Stackdriver) through the GCP handler. This guide covers installation, configuration, and best practices for using MickTrace with Google Cloud Platform.

## Installation

```bash
# Install MickTrace with GCP support
pip install micktrace[gcp]

# Or install all cloud platforms
pip install micktrace[cloud]
```

## Quick Start

### Basic Configuration

```python
import micktrace

# Configure GCP handler
micktrace.configure(
    level="INFO",
    handlers=[{
        "type": "gcp",  # or "stackdriver"
        "config": {
            "project_id": "my-gcp-project",
            "log_name": "my-application"
        }
    }]
)

logger = micktrace.get_logger(__name__)
logger.info("Hello from GCP!", user_id=123, action="login")
```

## Handler Types

MickTrace provides multiple ways to use GCP logging:

### 1. Handler Type in Configuration

```python
# Use 'gcp' (recommended)
handlers=[{"type": "gcp", "config": {...}}]

# Or use 'stackdriver' (legacy name)
handlers=[{"type": "stackdriver", "config": {...}}]
```

### 2. Direct Handler Import

```python
from micktrace.handlers import GoogleCloudHandler, GCPHandler, StackdriverHandler

# All three are aliases for the same handler
handler = GoogleCloudHandler(
    project_id="my-project",
    log_name="my-app"
)
```

### 3. Async Handler

```python
from micktrace.handlers import AsyncGCPHandler, AsyncGoogleCloudHandler

handler = AsyncGCPHandler(
    project_id="my-project",
    log_name="my-app",
    batch_size=100,
    flush_interval=5.0
)
```

## Configuration Options

### Basic Options

```python
{
    "type": "gcp",
    "config": {
        "project_id": "my-gcp-project",        # Required: GCP project ID
        "log_name": "my-application",          # Optional: Log name (default: "micktrace")
        "credentials_path": "/path/to/key.json", # Optional: Service account key
        "batch_size": 100,                     # Optional: Logs per batch (default: 100)
        "flush_interval": 5.0                  # Optional: Seconds between flushes (default: 5.0)
    }
}
```

### Resource Configuration

```python
{
    "type": "gcp",
    "config": {
        "project_id": "my-project",
        "log_name": "my-app",
        "resource": {
            "type": "cloud_function",  # Resource type
            "labels": {
                "function_name": "my-function",
                "region": "us-central1"
            }
        }
    }
}
```

## Authentication

### 1. Application Default Credentials (Recommended)

When running on GCP (Cloud Functions, Cloud Run, GKE), authentication is automatic:

```python
micktrace.configure(
    handlers=[{
        "type": "gcp",
        "config": {
            "project_id": "my-project",
            "log_name": "my-app"
        }
    }]
)
```

### 2. Service Account Key File

For local development or non-GCP environments:

```python
micktrace.configure(
    handlers=[{
        "type": "gcp",
        "config": {
            "project_id": "my-project",
            "log_name": "my-app",
            "credentials_path": "/path/to/service-account-key.json"
        }
    }]
)
```

### 3. Environment Variable

Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

Then use basic configuration without `credentials_path`.

## Use Cases

### Google Cloud Functions

```python
import micktrace

micktrace.configure(
    level="INFO",
    handlers=[{
        "type": "gcp",
        "config": {
            "project_id": "my-project",
            "log_name": "cloud-function-logs",
            "resource": {
                "type": "cloud_function",
                "labels": {
                    "function_name": "process-events",
                    "region": "us-central1"
                }
            }
        }
    }]
)

def cloud_function_handler(request):
    logger = micktrace.get_logger("function")
    logger.info("Function invoked", request_id=request.headers.get("X-Request-ID"))
    # Your function logic
    return "Success"
```

### Google Cloud Run

```python
import micktrace

micktrace.configure(
    level="INFO",
    handlers=[{
        "type": "gcp",
        "config": {
            "project_id": "my-project",
            "log_name": "cloud-run-service",
            "resource": {
                "type": "cloud_run_revision",
                "labels": {
                    "service_name": "api-service",
                    "revision_name": "api-service-v1",
                    "location": "us-central1"
                }
            }
        }
    }]
)

logger = micktrace.get_logger("api")
logger.info("Service started", port=8080)
```

### Google Kubernetes Engine (GKE)

```python
import micktrace

micktrace.configure(
    level="INFO",
    handlers=[{
        "type": "gcp",
        "config": {
            "project_id": "my-project",
            "log_name": "gke-cluster-logs",
            "resource": {
                "type": "k8s_pod",
                "labels": {
                    "cluster_name": "production-cluster",
                    "namespace_name": "default",
                    "pod_name": "app-deployment-abc123"
                }
            }
        }
    }]
)

logger = micktrace.get_logger("k8s")
logger.info("Pod started", container="app")
```

## Cloud Trace Integration

Integrate with Google Cloud Trace for distributed tracing:

```python
import micktrace

logger = micktrace.get_logger("traced_app")

# Add trace context to logs
trace_id = f"projects/my-project/traces/{trace_id_value}"
span_id = span_id_value

with micktrace.context(trace=trace_id, span_id=span_id):
    logger.info("Processing request", operation="fetch_data")
    # Logs will include trace and span IDs
```

## Structured Logging

GCP handler automatically converts structured data to JSON payload:

```python
logger = micktrace.get_logger("app")

logger.info(
    "User action",
    user_id=123,
    action="purchase",
    amount=99.99,
    currency="USD",
    items=["item1", "item2"]
)
```

This creates a log entry with:
- `message`: "User action"
- `jsonPayload`: Contains all structured fields

## Severity Levels

MickTrace levels map to GCP severity levels:

| MickTrace | GCP Severity |
|-----------|--------------|
| DEBUG     | DEBUG        |
| INFO      | INFO         |
| WARNING   | WARNING      |
| ERROR     | ERROR        |
| CRITICAL  | CRITICAL     |

## Best Practices

### 1. Use Structured Logging

```python
# Good: Structured data
logger.info("Order processed", order_id=123, total=99.99)

# Avoid: String formatting
logger.info(f"Order {123} processed with total {99.99}")
```

### 2. Set Appropriate Resource Types

Use the correct resource type for your environment:
- `cloud_function` for Cloud Functions
- `cloud_run_revision` for Cloud Run
- `k8s_pod` for GKE
- `gce_instance` for Compute Engine
- `global` for generic applications

### 3. Use Context for Request Tracking

```python
with micktrace.context(request_id=request_id, user_id=user_id):
    logger.info("Processing request")
    # All logs in this context include request_id and user_id
```

### 4. Batch Configuration

For high-throughput applications, adjust batching:

```python
{
    "type": "gcp",
    "config": {
        "project_id": "my-project",
        "log_name": "high-volume-app",
        "batch_size": 500,      # Larger batches
        "flush_interval": 10.0  # Less frequent flushes
    }
}
```

### 5. Error Handling

The GCP handler gracefully handles errors and continues logging:

```python
# Even if GCP logging fails, your application continues
logger.error("Critical error", error_code="E001")
```

## Troubleshooting

### Import Error

```
ImportError: google-cloud-logging library is required
```

**Solution**: Install GCP dependencies
```bash
pip install micktrace[gcp]
```

### Authentication Error

```
google.auth.exceptions.DefaultCredentialsError
```

**Solution**: Set up authentication
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

### Logs Not Appearing

1. Check project ID is correct
2. Verify service account has `roles/logging.logWriter` permission
3. Check log name in Cloud Logging console
4. Ensure flush interval hasn't been set too high

## Examples

See the complete example file:
- `examples/gcp_example.py` - Comprehensive GCP logging examples

## Additional Resources

- [Google Cloud Logging Documentation](https://cloud.google.com/logging/docs)
- [MickTrace README](../README.md)
- [Cloud Logging Python Client](https://googleapis.dev/python/logging/latest/)

## Support

For issues or questions:
- GitHub Issues: https://github.com/ajayagrawalgit/MickTrace/issues
- Documentation: https://github.com/ajayagrawalgit/MickTrace#readme
