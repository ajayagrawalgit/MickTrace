"""
MickTrace Context Example - Production Ready
===========================================

This example demonstrates MickTrace's bound loggers and context management
for production applications. Shows how to maintain context across function
calls and create specialized loggers for different components.
"""

import asyncio
import time
import micktrace


def simulate_user_service():
    """Simulate a user service with bound context."""
    print("=== User Service Example ===")

    # Configure micktrace
    micktrace.configure(
        level="INFO", format="structured", handlers=[{"type": "console"}]
    )

    # Create service logger with bound context
    service_logger = micktrace.get_logger("user_service").bind(
        service="user_service", version="1.2.3", environment="production"
    )

    # Simulate user operations
    users = [
        {"id": 1001, "name": "Alice Johnson", "role": "admin"},
        {"id": 1002, "name": "Bob Smith", "role": "user"},
        {"id": 1003, "name": "Carol Davis", "role": "moderator"},
    ]

    for user in users:
        # Create user-specific logger
        user_logger = service_logger.bind(
            user_id=user["id"], user_name=user["name"], user_role=user["role"]
        )

        # Log user operations with automatic context
        user_logger.info("User authentication started")

        # Simulate authentication process
        time.sleep(0.1)  # Simulate processing time

        if user["role"] == "admin":
            user_logger.info(
                "Admin privileges granted",
                permissions=["read", "write", "delete", "admin"],
            )
        elif user["role"] == "moderator":
            user_logger.info(
                "Moderator privileges granted",
                permissions=["read", "write", "moderate"],
            )
        else:
            user_logger.info("Standard user privileges granted",
                             permissions=["read"])

        user_logger.info("User authentication completed",
                         duration_ms=100, success=True)

    print("✅ User service simulation completed!")


def simulate_order_processing():
    """Simulate order processing with request-scoped context."""
    print("\n=== Order Processing Example ===")

    # Create order service logger
    order_logger = micktrace.get_logger("order_service").bind(
        service="order_service", version="2.1.0"
    )

    # Simulate order processing
    orders = [
        {"id": "ORD-001", "customer_id": 2001, "amount": 99.99, "items": 3},
        {"id": "ORD-002", "customer_id": 2002, "amount": 149.50, "items": 2},
        {"id": "ORD-003", "customer_id": 2001, "amount": 299.99, "items": 5},
    ]

    for order in orders:
        # Create order-specific logger with all context
        request_logger = order_logger.bind(
            order_id=order["id"],
            customer_id=order["customer_id"],
            order_amount=order["amount"],
            item_count=order["items"],
        )

        request_logger.info("Order processing started")

        # Simulate validation
        request_logger.debug("Validating order data")
        time.sleep(0.05)

        # Simulate inventory check
        inventory_logger = request_logger.bind(operation="inventory_check")
        inventory_logger.info("Checking inventory availability")
        time.sleep(0.1)
        inventory_logger.info("Inventory check completed", available=True)

        # Simulate payment processing
        payment_logger = request_logger.bind(operation="payment_processing")
        payment_logger.info("Processing payment")
        time.sleep(0.15)
        payment_logger.info(
            "Payment processed successfully", transaction_id=f"TXN-{order['id']}"
        )

        # Complete order
        request_logger.info(
            "Order processing completed", status="confirmed", processing_time_ms=300
        )

    print("✅ Order processing simulation completed!")


def simulate_error_scenarios():
    """Simulate error scenarios with proper context."""
    print("\n=== Error Handling Example ===")

    error_logger = micktrace.get_logger("error_service").bind(
        service="error_service", component="payment_gateway"
    )

    # Simulate various error scenarios
    error_scenarios = [
        {"type": "network_timeout", "severity": "warning", "retryable": True},
        {"type": "invalid_card", "severity": "error", "retryable": False},
        {"type": "service_unavailable", "severity": "critical", "retryable": True},
    ]

    for i, scenario in enumerate(error_scenarios):
        scenario_logger = error_logger.bind(
            error_id=f"ERR-{i+1:03d}",
            error_type=scenario["type"],
            retryable=scenario["retryable"],
        )

        if scenario["severity"] == "warning":
            scenario_logger.warning(
                "Service degradation detected",
                impact="increased_latency",
                action="monitoring",
            )
        elif scenario["severity"] == "error":
            scenario_logger.error(
                "Transaction failed", reason=scenario["type"], customer_notified=True
            )
        else:  # critical
            scenario_logger.critical(
                "Service outage detected",
                affected_regions=["us-east-1", "eu-west-1"],
                escalation_triggered=True,
            )

    print("✅ Error handling simulation completed!")


async def simulate_async_operations():
    """Simulate async operations with context propagation."""
    print("\n=== Async Operations Example ===")

    async_logger = micktrace.get_logger("async_service").bind(
        service="async_service", operation_type="background_task"
    )

    # Simulate concurrent operations
    async def process_task(task_id: int, duration: float):
        task_logger = async_logger.bind(
            task_id=f"TASK-{task_id:03d}", estimated_duration=duration
        )

        task_logger.info("Task started")
        await asyncio.sleep(duration)
        task_logger.info("Task completed", actual_duration=duration)
        return f"Result-{task_id}"

    # Run multiple tasks concurrently
    tasks = [process_task(1, 0.1), process_task(2, 0.2), process_task(3, 0.15)]

    results = await asyncio.gather(*tasks)

    async_logger.info(
        "All async tasks completed", task_count=len(tasks), results=results
    )

    print("✅ Async operations simulation completed!")


def main():
    """Main function demonstrating context management."""
    print("🚀 MickTrace Context Management Example")
    print("=" * 50)

    # Run synchronous examples
    simulate_user_service()
    simulate_order_processing()
    simulate_error_scenarios()

    # Run async example
    asyncio.run(simulate_async_operations())

    print("\n🎉 All context examples completed successfully!")
    print("💡 Notice how each logger maintains its bound context automatically")


if __name__ == "__main__":
    main()
