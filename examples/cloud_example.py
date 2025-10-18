"""
MickTrace Cloud Integration Example - Production Ready
=====================================================

This example demonstrates cloud logging patterns and best practices
using MickTrace. Shows how to structure logs for cloud environments.
"""

import json
import random
import time
import micktrace
from pathlib import Path


def simulate_aws_lambda_logging():
    """Simulate AWS Lambda function logging."""
    print("=== AWS Lambda Logging Simulation ===")

    # Configure structured logging for Lambda
    micktrace.configure(
        level="INFO",
        format="structured",
        handlers=[{"type": "console"}],  # Lambda uses CloudWatch automatically
    )

    lambda_logger = micktrace.get_logger("lambda_function").bind(
        service="user-service",
        version="1.2.3",
        environment="production",
        aws_region="us-east-1",
        function_name="process-user-events",
    )

    # Simulate Lambda event processing
    events = [
        {
            "eventName": "UserCreated",
            "userId": "user-001",
            "email": "alice@example.com",
        },
        {"eventName": "UserUpdated", "userId": "user-002", "email": "bob@example.com"},
        {
            "eventName": "UserDeleted",
            "userId": "user-003",
            "email": "carol@example.com",
        },
    ]

    for event in events:
        request_id = f"req-{random.randint(1000, 9999)}"

        # Create request-scoped logger
        request_logger = lambda_logger.bind(
            aws_request_id=request_id,
            event_name=event["eventName"],
            user_id=event["userId"],
        )

        request_logger.info("Lambda function invoked")

        # Simulate processing
        processing_start = time.time()
        time.sleep(random.uniform(0.1, 0.3))  # Simulate work
        processing_time = time.time() - processing_start

        # Log business logic
        if event["eventName"] == "UserCreated":
            request_logger.info(
                "Creating user profile", email=event["email"], profile_created=True
            )
        elif event["eventName"] == "UserUpdated":
            request_logger.info(
                "Updating user profile",
                email=event["email"],
                fields_updated=["email", "last_login"],
            )
        else:  # UserDeleted
            request_logger.warning(
                "Deleting user profile", email=event["email"], data_retention_days=30
            )

        # Log completion with metrics
        request_logger.info(
            "Lambda function completed",
            duration_ms=round(processing_time * 1000, 2),
            memory_used_mb=random.randint(128, 512),
            billed_duration_ms=round(processing_time * 1000),
        )
    print("✅ AWS Lambda simulation completed!")


def simulate_kubernetes_logging():
    """Simulate Kubernetes pod logging."""
    print("\n=== Kubernetes Pod Logging Simulation ===")

    k8s_logger = micktrace.get_logger("k8s_pod").bind(
        service="api-gateway",
        version="2.1.0",
        environment="production",
        cluster="prod-cluster",
        namespace="default",
        pod_name="api-gateway-7d4b8c9f-x2k8m",
        node_name="worker-node-01",
    )

    # Simulate pod lifecycle events
    k8s_logger.info(
        "Pod starting",
        container_image="api-gateway:2.1.0",
        resource_limits={"cpu": "500m", "memory": "512Mi"},
        restart_count=0,
    )

    # Simulate health checks
    for i in range(5):
        health_status = "healthy" if random.random() > 0.1 else "degraded"

        k8s_logger.info(
            "Health check",
            check_number=i + 1,
            status=health_status,
            response_time_ms=random.randint(5, 50),
            endpoint="/health",
        )

        if health_status == "degraded":
            k8s_logger.warning(
                "Service degradation detected",
                cpu_usage_percent=random.randint(80, 95),
                memory_usage_percent=random.randint(75, 90),
                active_connections=random.randint(800, 1000),
            )

    # Simulate traffic handling
    for i in range(10):
        request_logger = k8s_logger.bind(
            request_id=f"k8s-req-{i+1:03d}",
            client_ip=f"10.0.{random.randint(1, 255)}.{random.randint(1, 255)}",
        )

        request_logger.info(
            "Handling request",
            method="GET",
            path="/api/v1/users",
            user_agent="kubectl/1.21.0",
        )

        # Simulate response
        status_codes = [200, 200, 200, 200, 404, 500]  # Mostly successful
        status_code = random.choice(status_codes)
        response_time = random.uniform(10, 200)

        request_logger.info(
            "Request completed",
            status_code=status_code,
            response_time_ms=round(response_time, 2),
            bytes_sent=random.randint(500, 5000),
        )

    k8s_logger.info(
        "Pod running normally",
        uptime_seconds=3600,
        requests_handled=10,
        error_rate_percent=10.0,
    )

    print("✅ Kubernetes pod simulation completed!")
    print("📄 Logs written to logs/k8s_pod.log")


def simulate_microservices_tracing():
    """Simulate distributed microservices with tracing."""
    print("\n=== Microservices Distributed Tracing ===")

    # Configure console logging for tracing demo
    micktrace.configure(
        level="INFO", format="structured", handlers=[{"type": "console"}]
    )

    # Simulate distributed trace across services
    trace_id = f"trace-{random.randint(100000, 999999)}"

    # Service 1: API Gateway
    gateway_logger = micktrace.get_logger("api-gateway").bind(
        service="api-gateway", trace_id=trace_id, span_id="span-001"
    )

    gateway_logger.info(
        "Received client request",
        method="POST",
        path="/api/orders",
        client_id="client-12345",
    )

    # Service 2: User Service
    user_service_logger = micktrace.get_logger("user-service").bind(
        service="user-service",
        trace_id=trace_id,
        span_id="span-002",
        parent_span_id="span-001",
    )

    user_service_logger.info(
        "Validating user", user_id="user-67890", validation_type="authentication"
    )

    time.sleep(0.05)  # Simulate processing

    user_service_logger.info(
        "User validation completed", user_id="user-67890", is_valid=True, duration_ms=50
    )

    # Service 3: Order Service
    order_service_logger = micktrace.get_logger("order-service").bind(
        service="order-service",
        trace_id=trace_id,
        span_id="span-003",
        parent_span_id="span-001",
    )

    order_service_logger.info(
        "Creating order",
        order_id="order-abc123",
        user_id="user-67890",
        items_count=3,
        total_amount=99.99,
    )

    time.sleep(0.1)  # Simulate processing

    # Service 4: Payment Service
    payment_service_logger = micktrace.get_logger("payment-service").bind(
        service="payment-service",
        trace_id=trace_id,
        span_id="span-004",
        parent_span_id="span-003",
    )

    payment_service_logger.info(
        "Processing payment",
        payment_id="pay-xyz789",
        amount=99.99,
        payment_method="credit_card",
    )

    time.sleep(0.08)  # Simulate processing

    payment_service_logger.info(
        "Payment completed",
        payment_id="pay-xyz789",
        status="success",
        transaction_id="txn-456789",
    )

    # Complete order
    order_service_logger.info(
        "Order completed",
        order_id="order-abc123",
        status="confirmed",
        total_processing_time_ms=180,
    )

    # Complete gateway request
    gateway_logger.info(
        "Request completed",
        status_code=201,
        total_duration_ms=200,
        services_called=["user-service", "order-service", "payment-service"],
    )

    print("✅ Microservices tracing simulation completed!")


def simulate_cloud_monitoring():
    """Simulate cloud monitoring and alerting patterns."""
    print("\n=== Cloud Monitoring Simulation ===")

    monitor_logger = micktrace.get_logger("cloud-monitor").bind(
        service="monitoring-agent", cloud_provider="aws", region="us-west-2"
    )

    # Simulate various cloud metrics
    metrics = [
        {"name": "cpu_utilization", "value": 75.5,
            "threshold": 80, "unit": "percent"},
        {"name": "memory_usage", "value": 68.2,
            "threshold": 85, "unit": "percent"},
        {"name": "disk_usage", "value": 45.8, "threshold": 90, "unit": "percent"},
        {"name": "network_in", "value": 1250.5, "threshold": 2000, "unit": "mbps"},
        {"name": "error_rate", "value": 2.1, "threshold": 5.0, "unit": "percent"},
    ]

    for metric in metrics:
        metric_logger = monitor_logger.bind(
            metric_name=metric["name"],
            metric_value=metric["value"],
            threshold=metric["threshold"],
        )

        if metric["value"] > metric["threshold"] * 0.9:  # 90% of threshold
            metric_logger.warning(
                "Metric approaching threshold",
                current_value=metric["value"],
                threshold=metric["threshold"],
                percentage_of_threshold=round(
                    (metric["value"] / metric["threshold"]) * 100, 1
                ),
            )
        elif metric["value"] > metric["threshold"]:
            metric_logger.error(
                "Metric exceeded threshold",
                current_value=metric["value"],
                threshold=metric["threshold"],
                alert_triggered=True,
            )
        else:
            metric_logger.info(
                "Metric within normal range",
                current_value=metric["value"],
                threshold=metric["threshold"],
            )

    # Simulate auto-scaling event
    monitor_logger.info(
        "Auto-scaling triggered",
        trigger_metric="cpu_utilization",
        current_instances=3,
        target_instances=5,
        scaling_policy="target_tracking",
    )

    print("✅ Cloud monitoring simulation completed!")


def main():
    """Main function demonstrating cloud logging patterns."""
    print("🚀 MickTrace Cloud Integration Example")
    print("=" * 50)

    # Run cloud simulations
    simulate_aws_lambda_logging()
    simulate_kubernetes_logging()
    simulate_microservices_tracing()
    simulate_cloud_monitoring()

    print("\n🎉 All cloud examples completed successfully!")
    print("💡 Cloud logging requires structured data and proper context")


if __name__ == "__main__":
    main()
