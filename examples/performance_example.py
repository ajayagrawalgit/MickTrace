"""
MickTrace Performance Example - Production Ready
===============================================

This example demonstrates performance monitoring and metrics logging
using MickTrace in production applications. Shows timing, throughput,
and performance tracking patterns.
"""

import asyncio
import random
import time
import micktrace


def performance_timer(func):
    """Simple performance timing decorator."""

    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger = micktrace.get_logger(func.__module__)
            logger.info(
                f"Function completed: {func.__name__}",
                function=func.__name__,
                duration_ms=round(duration * 1000, 2),
                success=True,
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger = micktrace.get_logger(func.__module__)
            logger.error(
                f"Function failed: {func.__name__}",
                function=func.__name__,
                duration_ms=round(duration * 1000, 2),
                error_type=type(e).__name__,
                success=False,
            )
            raise

    return wrapper


async def async_performance_timer(func):
    """Simple async performance timing decorator."""

    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger = micktrace.get_logger(func.__module__)
            logger.info(
                f"Async function completed: {func.__name__}",
                function=func.__name__,
                duration_ms=round(duration * 1000, 2),
                success=True,
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger = micktrace.get_logger(func.__module__)
            logger.error(
                f"Async function failed: {func.__name__}",
                function=func.__name__,
                duration_ms=round(duration * 1000, 2),
                error_type=type(e).__name__,
                success=False,
            )
            raise

    return wrapper


@performance_timer
def process_batch(items):
    """Process a batch of items with timing."""
    time.sleep(random.uniform(0.05, 0.15))  # Simulate work
    return [item * 2 for item in items]


@performance_timer
def database_query(query, table):
    """Simulate a database query with performance logging."""
    # Simulate database processing time
    processing_time = random.uniform(0.02, 0.08)
    time.sleep(processing_time)

    # Simulate different query results
    if "SELECT" in query.upper():
        return {"rows": random.randint(1, 100), "query_time": processing_time}
    elif "INSERT" in query.upper():
        return {"affected_rows": 1, "query_time": processing_time}
    else:
        return {"status": "executed", "query_time": processing_time}


def simulate_batch_processing():
    """Simulate batch processing with performance monitoring."""
    print("=== Batch Processing Performance ===")

    # Configure logging
    micktrace.configure(
        level="INFO", format="structured", handlers=[{"type": "console"}]
    )

    batch_logger = micktrace.get_logger("batch_processor").bind(
        component="batch_processor", version="1.0.0"
    )

    # Process multiple batches
    batch_sizes = [10, 50, 100, 200]
    total_items = 0
    total_time = 0

    for batch_size in batch_sizes:
        batch_start = time.time()

        # Create batch data
        batch_data = list(range(batch_size))

        batch_logger.info(
            "Starting batch processing",
            batch_size=batch_size,
            batch_id=f"BATCH-{batch_size}",
        )

        # Process the batch
        result = process_batch(batch_data)

        batch_duration = time.time() - batch_start
        total_items += batch_size
        total_time += batch_duration

        # Log batch completion with metrics
        batch_logger.info(
            "Batch processing completed",
            batch_size=batch_size,
            items_processed=len(result),
            batch_duration_ms=round(batch_duration * 1000, 2),
            throughput_items_per_sec=round(batch_size / batch_duration, 2),
        )

    # Log overall performance summary
    batch_logger.info(
        "All batches completed",
        total_batches=len(batch_sizes),
        total_items=total_items,
        total_duration_ms=round(total_time * 1000, 2),
        average_throughput=round(total_items / total_time, 2),
    )

    print("✅ Batch processing simulation completed!")


def simulate_database_performance():
    """Simulate database operations with performance monitoring."""
    print("\n=== Database Performance Monitoring ===")

    db_logger = micktrace.get_logger("database").bind(
        component="database", connection_pool="primary"
    )

    # Simulate various database operations
    queries = [
        ("SELECT * FROM users WHERE active = 1", "users"),
        ("INSERT INTO logs (message, level) VALUES (?, ?)", "logs"),
        ("UPDATE users SET last_login = NOW() WHERE id = ?", "users"),
        ("SELECT COUNT(*) FROM orders WHERE date > ?", "orders"),
        ("DELETE FROM temp_data WHERE created < ?", "temp_data"),
    ]

    total_queries = 0
    total_time = 0
    slow_queries = 0

    for query, table in queries:
        query_start = time.time()

        # Log query start
        query_logger = db_logger.bind(
            query_id=f"Q{total_queries + 1:03d}",
            table=table,
            operation=query.split()[0],
        )

        query_logger.debug("Executing database query", query=query[:50] + "...")

        # Execute query
        result = database_query(query, table)

        query_duration = time.time() - query_start
        total_queries += 1
        total_time += query_duration

        # Check if query is slow (>50ms)
        if query_duration > 0.05:
            slow_queries += 1
            query_logger.warning(
                "Slow query detected",
                duration_ms=round(query_duration * 1000, 2),
                threshold_ms=50,
                needs_optimization=True,
            )
        else:
            query_logger.info(
                "Query completed",
                duration_ms=round(query_duration * 1000, 2),
                result_summary=result,
            )

    # Log database performance summary
    db_logger.info(
        "Database session completed",
        total_queries=total_queries,
        total_duration_ms=round(total_time * 1000, 2),
        average_query_time_ms=round((total_time / total_queries) * 1000, 2),
        slow_queries=slow_queries,
        slow_query_percentage=round((slow_queries / total_queries) * 100, 2),
    )

    print("✅ Database performance simulation completed!")


async def simulate_async_performance():
    """Simulate async operations with performance monitoring."""
    print("\n=== Async Performance Monitoring ===")

    async_logger = micktrace.get_logger("async_service").bind(
        component="async_service", worker_pool="default"
    )

    async def async_task(task_id: int, complexity: str):
        """Simulate an async task with variable complexity."""
        task_logger = async_logger.bind(
            task_id=f"ASYNC-{task_id:03d}", complexity=complexity
        )

        # Simulate different processing times based on complexity
        if complexity == "simple":
            await asyncio.sleep(random.uniform(0.01, 0.05))
        elif complexity == "medium":
            await asyncio.sleep(random.uniform(0.05, 0.15))
        else:  # complex
            await asyncio.sleep(random.uniform(0.15, 0.30))

        return f"Result-{task_id}"

    # Create tasks with different complexities
    tasks = []
    complexities = ["simple", "medium", "complex"]

    for i in range(12):
        complexity = complexities[i % 3]
        tasks.append(async_task(i + 1, complexity))

    async_logger.info(
        "Starting async task batch",
        total_tasks=len(tasks),
        complexity_distribution={
            "simple": len([t for i, t in enumerate(tasks) if i % 3 == 0]),
            "medium": len([t for i, t in enumerate(tasks) if i % 3 == 1]),
            "complex": len([t for i, t in enumerate(tasks) if i % 3 == 2]),
        },
    )

    # Execute all tasks concurrently and measure performance
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    total_duration = time.time() - start_time

    async_logger.info(
        "Async task batch completed",
        total_tasks=len(tasks),
        total_duration_ms=round(total_duration * 1000, 2),
        tasks_per_second=round(len(tasks) / total_duration, 2),
        results_count=len(results),
    )

    print("✅ Async performance simulation completed!")


def simulate_error_performance():
    """Simulate error scenarios with performance impact."""
    print("\n=== Error Performance Impact ===")

    error_logger = micktrace.get_logger("error_service").bind(
        component="error_handler", retry_policy="exponential_backoff"
    )

    def unreliable_operation(operation_id: int, failure_rate: float = 0.3):
        """Simulate an unreliable operation."""
        start_time = time.time()

        # Simulate processing
        time.sleep(random.uniform(0.02, 0.08))

        # Randomly fail based on failure rate
        if random.random() < failure_rate:
            duration = time.time() - start_time
            error_logger.error(
                "Operation failed",
                operation_id=operation_id,
                duration_ms=round(duration * 1000, 2),
                failure_rate=failure_rate,
                retry_recommended=True,
            )
            raise RuntimeError(f"Operation {operation_id} failed")

        duration = time.time() - start_time
        error_logger.info(
            "Operation succeeded",
            operation_id=operation_id,
            duration_ms=round(duration * 1000, 2),
        )
        return f"Success-{operation_id}"

    # Test different failure rates
    failure_rates = [0.1, 0.3, 0.5]

    for failure_rate in failure_rates:
        successes = 0
        failures = 0
        total_attempts = 20

        error_logger.info(
            "Testing failure rate",
            failure_rate=failure_rate,
            total_attempts=total_attempts,
        )

        for i in range(total_attempts):
            try:
                unreliable_operation(i + 1, failure_rate)
                successes += 1
            except RuntimeError:
                failures += 1

        # Log failure rate analysis
        actual_failure_rate = failures / total_attempts
        error_logger.info(
            "Failure rate test completed",
            expected_failure_rate=failure_rate,
            actual_failure_rate=round(actual_failure_rate, 2),
            successes=successes,
            failures=failures,
            variance=round(abs(failure_rate - actual_failure_rate), 2),
        )

    print("✅ Error performance simulation completed!")


def main():
    """Main function demonstrating performance monitoring."""
    print("🚀 MickTrace Performance Monitoring Example")
    print("=" * 50)

    # Run synchronous performance tests
    simulate_batch_processing()
    simulate_database_performance()
    simulate_error_performance()

    # Run async performance test
    asyncio.run(simulate_async_performance())

    print("\n🎉 All performance examples completed successfully!")
    print("💡 Performance metrics are automatically logged with context")


if __name__ == "__main__":
    main()
