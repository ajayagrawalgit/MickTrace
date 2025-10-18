"""
MickTrace Google Cloud Platform (GCP) Logging Example
======================================================

This example demonstrates how to use MickTrace with Google Cloud Logging
(formerly Stackdriver). Shows configuration, structured logging, and
best practices for GCP environments.

Requirements:
    pip install micktrace[gcp]

Environment Setup:
    - Set GOOGLE_APPLICATION_CREDENTIALS to your service account key file
    - Or run on GCP (Cloud Functions, Cloud Run, GKE) with default credentials
"""

import micktrace
import time
import random


def example_basic_gcp_logging():
    """Basic GCP logging configuration."""
    print("=== Basic GCP Logging ===\n")
    
    # Configure MickTrace to send logs to Google Cloud Logging
    micktrace.configure(
        level="INFO",
        handlers=[
            {"type": "console"},  # Also log to console for debugging
            {
                "type": "gcp",  # Use 'gcp' or 'stackdriver'
                "config": {
                    "project_id": "my-gcp-project",
                    "log_name": "micktrace-app",
                    # Optional: credentials_path="/path/to/service-account.json"
                }
            }
        ]
    )
    
    logger = micktrace.get_logger("gcp_example")
    
    logger.info("Application started", version="1.0.0", environment="production")
    logger.debug("Debug information", debug_mode=False)
    logger.warning("Resource usage high", cpu_percent=85, memory_mb=1024)
    logger.error("Failed to process request", error_code="E001", retry_count=3)
    
    print("\n")


def example_cloud_function_logging():
    """Simulate Google Cloud Function logging."""
    print("=== Cloud Function Logging ===\n")
    
    micktrace.configure(
        level="INFO",
        format="structured",
        handlers=[
            {
                "type": "gcp",
                "config": {
                    "project_id": "my-gcp-project",
                    "log_name": "cloud-function-logs",
                    "resource_type": "cloud_function",
                    "resource_labels": {
                        "function_name": "process-events",
                        "region": "us-central1"
                    }
                }
            }
        ]
    )
    
    function_logger = micktrace.get_logger("cloud_function").bind(
        service="event-processor",
        version="2.1.0",
        environment="production"
    )
    
    # Simulate processing events
    events = [
        {"event_type": "user.created", "user_id": "user-123"},
        {"event_type": "order.placed", "order_id": "order-456"},
        {"event_type": "payment.processed", "payment_id": "pay-789"}
    ]
    
    for event in events:
        execution_id = f"exec-{random.randint(1000, 9999)}"
        
        with micktrace.context(execution_id=execution_id, event_type=event["event_type"]):
            function_logger.info("Function invoked", event=event)
            
            # Simulate processing
            start_time = time.time()
            time.sleep(random.uniform(0.05, 0.15))
            duration_ms = (time.time() - start_time) * 1000
            
            function_logger.info(
                "Event processed successfully",
                duration_ms=round(duration_ms, 2),
                status="success"
            )
    
    print("\n")


def example_cloud_run_logging():
    """Simulate Google Cloud Run service logging."""
    print("=== Cloud Run Service Logging ===\n")
    
    micktrace.configure(
        level="INFO",
        handlers=[
            {
                "type": "gcp",
                "config": {
                    "project_id": "my-gcp-project",
                    "log_name": "cloud-run-service",
                    "resource_type": "cloud_run_revision",
                    "resource_labels": {
                        "service_name": "api-service",
                        "revision_name": "api-service-v1",
                        "location": "us-central1"
                    }
                }
            }
        ]
    )
    
    api_logger = micktrace.get_logger("api_service").bind(
        service="user-api",
        version="3.0.0"
    )
    
    # Simulate API requests
    requests = [
        {"method": "GET", "path": "/api/users/123", "status": 200},
        {"method": "POST", "path": "/api/users", "status": 201},
        {"method": "PUT", "path": "/api/users/456", "status": 200},
        {"method": "DELETE", "path": "/api/users/789", "status": 204}
    ]
    
    for req in requests:
        request_id = f"req-{random.randint(10000, 99999)}"
        
        with micktrace.context(
            request_id=request_id,
            method=req["method"],
            path=req["path"]
        ):
            api_logger.info("Request received")
            
            # Simulate request processing
            start_time = time.time()
            time.sleep(random.uniform(0.02, 0.08))
            response_time_ms = (time.time() - start_time) * 1000
            
            api_logger.info(
                "Request completed",
                status_code=req["status"],
                response_time_ms=round(response_time_ms, 2)
            )
    
    print("\n")


def example_gke_logging():
    """Simulate Google Kubernetes Engine (GKE) logging."""
    print("=== GKE Pod Logging ===\n")
    
    micktrace.configure(
        level="INFO",
        handlers=[
            {
                "type": "gcp",
                "config": {
                    "project_id": "my-gcp-project",
                    "log_name": "gke-cluster-logs",
                    "resource_type": "k8s_pod",
                    "resource_labels": {
                        "cluster_name": "production-cluster",
                        "namespace_name": "default",
                        "pod_name": "app-deployment-abc123"
                    }
                }
            }
        ]
    )
    
    pod_logger = micktrace.get_logger("k8s_pod").bind(
        app="backend-service",
        version="4.2.1",
        environment="production",
        pod_ip="10.0.1.42"
    )
    
    pod_logger.info("Pod started", container="app", image="gcr.io/project/app:v4.2.1")
    pod_logger.info("Health check passed", endpoint="/health", status="healthy")
    pod_logger.info("Connected to database", db_host="postgres.default.svc", db_name="appdb")
    pod_logger.warning("High memory usage detected", memory_percent=78, threshold=75)
    
    print("\n")


def example_trace_integration():
    """Example with Cloud Trace integration."""
    print("=== Cloud Trace Integration ===\n")
    
    micktrace.configure(
        level="INFO",
        handlers=[
            {
                "type": "gcp",
                "config": {
                    "project_id": "my-gcp-project",
                    "log_name": "traced-application"
                }
            }
        ]
    )
    
    logger = micktrace.get_logger("traced_app")
    
    # Simulate distributed trace
    trace_id = f"projects/my-gcp-project/traces/{random.randint(100000, 999999)}"
    span_id = f"{random.randint(1000000, 9999999)}"
    
    with micktrace.context(trace=trace_id, span_id=span_id):
        logger.info("Processing distributed request", operation="fetch_user_data")
        
        # Simulate sub-operations
        logger.debug("Querying database", query="SELECT * FROM users WHERE id = ?")
        logger.debug("Fetching from cache", cache_key="user:123")
        logger.info("Request completed", cache_hit=True, latency_ms=45)
    
    print("\n")


def main():
    """Run all GCP logging examples."""
    print("\n" + "="*60)
    print("MickTrace Google Cloud Platform Logging Examples")
    print("="*60 + "\n")
    
    print("Note: These examples require Google Cloud credentials.")
    print("Set GOOGLE_APPLICATION_CREDENTIALS or run on GCP.\n")
    
    try:
        example_basic_gcp_logging()
        example_cloud_function_logging()
        example_cloud_run_logging()
        example_gke_logging()
        example_trace_integration()
        
        print("="*60)
        print("All examples completed successfully!")
        print("="*60)
        
    except ImportError as e:
        print(f"\nError: {e}")
        print("\nPlease install GCP dependencies:")
        print("  pip install micktrace[gcp]")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you have valid GCP credentials configured.")


if __name__ == "__main__":
    main()
