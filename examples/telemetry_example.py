"""
MickTrace Telemetry Example - Production Ready
==============================================

This example demonstrates telemetry and observability patterns
using MickTrace without external dependencies.
"""

import random
import time
import micktrace
from uuid import uuid4


def simulate_distributed_tracing():
    """Simulate distributed tracing across services."""
    print("=== Distributed Tracing Simulation ===")

    # Configure logging
    micktrace.configure(
        level="INFO", format="structured", handlers=[{"type": "console"}]
    )

    # Generate trace ID for the entire request
    trace_id = str(uuid4())

    # Service 1: API Gateway
    gateway_logger = micktrace.get_logger("api-gateway").bind(
        service="api-gateway", trace_id=trace_id, span_id="span-001"
    )

    gateway_logger.info(
        "Request received", method="POST", path="/api/orders", client_id="client-12345"
    )

    # Service 2: Authentication Service
    auth_logger = micktrace.get_logger("auth-service").bind(
        service="auth-service",
        trace_id=trace_id,
        span_id="span-002",
        parent_span_id="span-001",
    )

    auth_logger.info("Authenticating user", user_id="user-67890")
    time.sleep(0.05)  # Simulate auth time
    auth_logger.info("Authentication successful",
                     user_id="user-67890", duration_ms=50)

    # Service 3: Order Service
    order_logger = micktrace.get_logger("order-service").bind(
        service="order-service",
        trace_id=trace_id,
        span_id="span-003",
        parent_span_id="span-001",
    )

    order_logger.info(
        "Creating order", order_id="order-abc123", user_id="user-67890", items_count=3
    )

    time.sleep(0.1)  # Simulate order processing

    # Service 4: Payment Service
    payment_logger = micktrace.get_logger("payment-service").bind(
        service="payment-service",
        trace_id=trace_id,
        span_id="span-004",
        parent_span_id="span-003",
    )

    payment_logger.info("Processing payment",
                        payment_id="pay-xyz789", amount=99.99)

    time.sleep(0.08)  # Simulate payment processing
    payment_logger.info("Payment completed",
                        payment_id="pay-xyz789", status="success")

    # Complete order
    order_logger.info("Order completed",
                      order_id="order-abc123", status="confirmed")

    # Complete gateway request
    gateway_logger.info("Request completed",
                        status_code=201, total_duration_ms=230)

    print("✅ Distributed tracing simulation completed!")


def simulate_metrics_collection():
    """Simulate metrics collection and logging."""
    print("\n=== Metrics Collection Simulation ===")

    metrics_logger = micktrace.get_logger("metrics-collector").bind(
        component="metrics-collector", version="1.0.0"
    )

    # Simulate collecting various metrics
    services = ["api-gateway", "auth-service",
                "order-service", "payment-service"]

    for service in services:
        service_logger = metrics_logger.bind(service=service)

        # CPU metrics
        cpu_usage = random.uniform(20, 90)
        service_logger.info(
            "CPU metrics collected",
            metric_type="cpu_usage",
            value=round(cpu_usage, 2),
            unit="percent",
            timestamp=time.time(),
        )

        # Memory metrics
        memory_usage = random.uniform(30, 85)
        service_logger.info(
            "Memory metrics collected",
            metric_type="memory_usage",
            value=round(memory_usage, 2),
            unit="percent",
            timestamp=time.time(),
        )

        # Request rate metrics
        request_rate = random.uniform(100, 1000)
        service_logger.info(
            "Request rate metrics collected",
            metric_type="requests_per_second",
            value=round(request_rate, 2),
            unit="requests/sec",
            timestamp=time.time(),
        )

        # Error rate metrics
        error_rate = random.uniform(0.1, 5.0)
        service_logger.info(
            "Error rate metrics collected",
            metric_type="error_rate",
            value=round(error_rate, 2),
            unit="percent",
            timestamp=time.time(),
        )

        # Alert if metrics are concerning
        if cpu_usage > 80:
            service_logger.warning(
                "High CPU usage detected",
                current_value=round(cpu_usage, 2),
                threshold=80,
                alert_triggered=True,
            )

        if error_rate > 3.0:
            service_logger.error(
                "High error rate detected",
                current_value=round(error_rate, 2),
                threshold=3.0,
                alert_triggered=True,
            )

    print("✅ Metrics collection simulation completed!")


def simulate_application_performance_monitoring():
    """Simulate APM-style monitoring."""
    print("\n=== Application Performance Monitoring ===")

    apm_logger = micktrace.get_logger("apm-monitor").bind(
        component="apm-monitor", environment="production"
    )

    # Simulate monitoring different endpoints
    endpoints = [
        {"path": "/api/users", "method": "GET", "avg_response_time": 45},
        {"path": "/api/orders", "method": "POST", "avg_response_time": 120},
        {"path": "/api/payments", "method": "POST", "avg_response_time": 200},
        {"path": "/api/reports", "method": "GET", "avg_response_time": 300},
    ]

    for endpoint in endpoints:
        endpoint_logger = apm_logger.bind(
            endpoint_path=endpoint["path"], http_method=endpoint["method"]
        )

        # Simulate response time variations
        base_time = endpoint["avg_response_time"]
        actual_time = base_time + \
            random.uniform(-base_time * 0.3, base_time * 0.5)

        # Simulate different status codes
        status_codes = [200, 200, 200, 200, 201, 400, 404, 500]
        status_code = random.choice(status_codes)

        if status_code < 400:
            endpoint_logger.info(
                "Request processed successfully",
                status_code=status_code,
                response_time_ms=round(actual_time, 2),
                throughput_ok=True,
            )
        elif status_code < 500:
            endpoint_logger.warning(
                "Client error detected",
                status_code=status_code,
                response_time_ms=round(actual_time, 2),
                error_type="client_error",
            )
        else:
            endpoint_logger.error(
                "Server error detected",
                status_code=status_code,
                response_time_ms=round(actual_time, 2),
                error_type="server_error",
                requires_investigation=True,
            )

        # Performance analysis
        if actual_time > base_time * 1.5:
            endpoint_logger.warning(
                "Slow response detected",
                response_time_ms=round(actual_time, 2),
                baseline_ms=base_time,
                performance_degradation=True,
            )

    print("✅ APM simulation completed!")


def simulate_business_metrics():
    """Simulate business metrics and KPI tracking."""
    print("\n=== Business Metrics Tracking ===")

    business_logger = micktrace.get_logger("business-metrics").bind(
        component="business-analytics", dashboard="executive"
    )

    # Simulate daily business metrics
    daily_metrics = {
        "new_users": random.randint(50, 200),
        "active_users": random.randint(1000, 5000),
        "orders_placed": random.randint(100, 500),
        "revenue_usd": round(random.uniform(10000, 50000), 2),
        "conversion_rate": round(random.uniform(2.5, 8.5), 2),
    }

    business_logger.info(
        "Daily business metrics",
        **daily_metrics,
        metric_date=time.strftime("%Y-%m-%d"),
        collection_time=time.time(),
    )

    # Simulate hourly metrics
    for hour in range(0, 24, 4):  # Every 4 hours
        hourly_metrics = {
            "hour": hour,
            "page_views": random.randint(500, 2000),
            "api_calls": random.randint(1000, 10000),
            "error_count": random.randint(5, 50),
            "avg_response_time_ms": round(random.uniform(50, 300), 2),
        }

        hour_logger = business_logger.bind(hour=hour)
        hour_logger.info("Hourly metrics collected", **hourly_metrics)

        # Business alerts
        if hourly_metrics["error_count"] > 30:
            hour_logger.error(
                "High error count detected",
                error_count=hourly_metrics["error_count"],
                threshold=30,
                business_impact="high",
            )

        if hourly_metrics["avg_response_time_ms"] > 250:
            hour_logger.warning(
                "Performance degradation",
                avg_response_time_ms=hourly_metrics["avg_response_time_ms"],
                threshold_ms=250,
                user_experience_impact=True,
            )

    print("✅ Business metrics simulation completed!")


def simulate_security_monitoring():
    """Simulate security event monitoring."""
    print("\n=== Security Monitoring ===")

    security_logger = micktrace.get_logger("security-monitor").bind(
        component="security-monitor", environment="production"
    )

    # Simulate various security events
    security_events = [
        {
            "event_type": "login_attempt",
            "user_id": "user_12345",
            "ip_address": "192.168.1.100",
            "success": True,
            "method": "password",
        },
        {
            "event_type": "failed_login",
            "user_id": "user_67890",
            "ip_address": "10.0.0.50",
            "success": False,
            "attempt_count": 3,
            "method": "password",
        },
        {
            "event_type": "suspicious_activity",
            "user_id": "user_99999",
            "ip_address": "203.0.113.1",
            "activity": "multiple_failed_logins",
            "count": 10,
            "time_window_minutes": 5,
        },
        {
            "event_type": "privilege_escalation",
            "user_id": "user_admin",
            "ip_address": "192.168.1.200",
            "from_role": "user",
            "to_role": "admin",
            "authorized": True,
        },
    ]

    for event in security_events:
        event_logger = security_logger.bind(
            event_type=event["event_type"],
            user_id=event.get("user_id"),
            ip_address=event.get("ip_address"),
        )

        if event["event_type"] == "login_attempt" and event["success"]:
            event_logger.info(
                "Successful login", method=event["method"], security_level="normal"
            )

        elif event["event_type"] == "failed_login":
            event_logger.warning(
                "Failed login attempt",
                attempt_count=event["attempt_count"],
                method=event["method"],
                security_concern="moderate",
            )

        elif event["event_type"] == "suspicious_activity":
            event_logger.error(
                "Suspicious activity detected",
                activity=event["activity"],
                count=event["count"],
                time_window_minutes=event["time_window_minutes"],
                security_concern="high",
                action_required=True,
            )

        elif event["event_type"] == "privilege_escalation":
            if event["authorized"]:
                event_logger.info(
                    "Authorized privilege escalation",
                    from_role=event["from_role"],
                    to_role=event["to_role"],
                    security_level="monitored",
                )
            else:
                event_logger.critical(
                    "Unauthorized privilege escalation",
                    from_role=event["from_role"],
                    to_role=event["to_role"],
                    security_concern="critical",
                    immediate_action_required=True,
                )

    print("✅ Security monitoring simulation completed!")


def main():
    """Main function demonstrating telemetry patterns."""
    print("🚀 MickTrace Telemetry Example")
    print("=" * 45)

    # Run all telemetry simulations
    simulate_distributed_tracing()
    simulate_metrics_collection()
    simulate_application_performance_monitoring()
    simulate_business_metrics()
    simulate_security_monitoring()

    print("\n🎉 All telemetry examples completed successfully!")
    print("💡 Telemetry provides comprehensive observability into your systems")


if __name__ == "__main__":
    main()
