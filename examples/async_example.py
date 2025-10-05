"""
MickTrace Async Example - Production Ready
==========================================

This example demonstrates async logging patterns with MickTrace.
Shows how to use MickTrace in async/await applications.
"""

import asyncio
import random
import time
import micktrace


async def async_database_operation(operation_id: int):
    """Simulate an async database operation."""
    logger = micktrace.get_logger("database").bind(
        operation_id=f"DB-{operation_id:03d}", operation_type="query"
    )

    logger.info("Database operation started")

    # Simulate async database work
    processing_time = random.uniform(0.1, 0.3)
    await asyncio.sleep(processing_time)

    # Simulate occasional failures
    if random.random() < 0.1:  # 10% failure rate
        logger.error(
            "Database operation failed",
            error_code="DB_TIMEOUT",
            duration_ms=round(processing_time * 1000, 2),
        )
        raise Exception(f"Database timeout for operation {operation_id}")

    logger.info(
        "Database operation completed",
        duration_ms=round(processing_time * 1000, 2),
        rows_affected=random.randint(1, 100),
    )

    return f"Result-{operation_id}"


async def async_api_call(api_endpoint: str, request_id: str):
    """Simulate an async API call."""
    logger = micktrace.get_logger("api_client").bind(
        endpoint=api_endpoint, request_id=request_id, method="GET"
    )

    logger.info("API request started")

    # Simulate network latency
    latency = random.uniform(0.05, 0.2)
    await asyncio.sleep(latency)

    # Simulate different response codes
    status_codes = [200, 200, 200, 200, 404, 500]  # Mostly successful
    status_code = random.choice(status_codes)

    if status_code == 200:
        logger.info(
            "API request successful",
            status_code=status_code,
            response_time_ms=round(latency * 1000, 2),
            response_size_bytes=random.randint(500, 5000),
        )
    elif status_code == 404:
        logger.warning(
            "API resource not found",
            status_code=status_code,
            response_time_ms=round(latency * 1000, 2),
        )
    else:
        logger.error(
            "API request failed",
            status_code=status_code,
            response_time_ms=round(latency * 1000, 2),
            retry_recommended=True,
        )

    return {"status": status_code, "data": f"Response from {api_endpoint}"}


async def process_user_request(user_id: int, request_type: str):
    """Process a user request with multiple async operations."""
    request_logger = micktrace.get_logger("request_processor").bind(
        user_id=user_id,
        request_type=request_type,
        request_id=f"REQ-{user_id}-{int(time.time())}",
    )

    request_logger.info("Processing user request")

    try:
        # Perform multiple async operations concurrently
        tasks = [
            async_database_operation(user_id),
            async_api_call(f"/api/users/{user_id}", f"api-{user_id}"),
            async_api_call(f"/api/preferences/{user_id}", f"pref-{user_id}"),
        ]

        # Wait for all operations to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful_operations = 0
        failed_operations = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_operations += 1
                request_logger.warning(
                    f"Operation {i+1} failed",
                    operation_index=i + 1,
                    error_type=type(result).__name__,
                )
            else:
                successful_operations += 1

        request_logger.info(
            "User request completed",
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            total_operations=len(tasks),
        )

        return {
            "user_id": user_id,
            "success": successful_operations > 0,
            "results": results,
        }

    except Exception as e:
        request_logger.error(
            "Request processing failed",
            error_type=type(e).__name__,
            error_message=str(e),
        )
        raise


async def simulate_concurrent_requests():
    """Simulate multiple concurrent user requests."""
    print("=== Concurrent Request Processing ===")

    # Configure logging
    micktrace.configure(
        level="INFO", format="structured", handlers=[{"type": "console"}]
    )

    main_logger = micktrace.get_logger("main").bind(
        component="request_simulator", version="1.0.0"
    )

    # Create multiple concurrent requests
    request_types = ["profile_update", "data_export", "preferences", "analytics"]
    user_ids = range(1001, 1011)  # 10 users

    tasks = []
    for user_id in user_ids:
        request_type = random.choice(request_types)
        tasks.append(process_user_request(user_id, request_type))

    main_logger.info(
        "Starting concurrent request processing",
        total_requests=len(tasks),
        user_count=len(user_ids),
    )

    start_time = time.time()

    # Process all requests concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    total_time = time.time() - start_time

    # Analyze results
    successful_requests = sum(1 for r in results if not isinstance(r, Exception))
    failed_requests = len(results) - successful_requests

    main_logger.info(
        "Concurrent processing completed",
        total_requests=len(tasks),
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        total_time_ms=round(total_time * 1000, 2),
        requests_per_second=round(len(tasks) / total_time, 2),
    )

    print("✅ Concurrent request simulation completed!")


async def simulate_async_batch_processing():
    """Simulate async batch processing with logging."""
    print("\n=== Async Batch Processing ===")

    batch_logger = micktrace.get_logger("batch_processor").bind(
        component="async_batch_processor", batch_type="data_processing"
    )

    async def process_batch_item(item_id: int, batch_id: str):
        """Process a single batch item."""
        item_logger = batch_logger.bind(
            item_id=f"ITEM-{item_id:04d}", batch_id=batch_id
        )

        # Simulate processing time
        processing_time = random.uniform(0.02, 0.1)
        await asyncio.sleep(processing_time)

        item_logger.debug(
            "Item processed", processing_time_ms=round(processing_time * 1000, 2)
        )

        return f"Processed-{item_id}"

    # Process multiple batches
    batch_sizes = [50, 100, 75]

    for batch_num, batch_size in enumerate(batch_sizes, 1):
        batch_id = f"BATCH-{batch_num:02d}"

        batch_logger.info(
            "Starting batch processing", batch_id=batch_id, batch_size=batch_size
        )

        start_time = time.time()

        # Create tasks for all items in the batch
        tasks = [process_batch_item(item_id, batch_id) for item_id in range(batch_size)]

        # Process all items concurrently
        results = await asyncio.gather(*tasks)

        batch_time = time.time() - start_time

        batch_logger.info(
            "Batch processing completed",
            batch_id=batch_id,
            items_processed=len(results),
            batch_time_ms=round(batch_time * 1000, 2),
            throughput_items_per_sec=round(batch_size / batch_time, 2),
        )

    print("✅ Async batch processing simulation completed!")


async def main():
    """Main async function demonstrating various patterns."""
    print("🚀 MickTrace Async Example")
    print("=" * 40)

    # Run async simulations
    await simulate_concurrent_requests()
    await simulate_async_batch_processing()

    print("\n🎉 All async examples completed successfully!")
    print("💡 All logging was done asynchronously with proper context")


if __name__ == "__main__":
    asyncio.run(main())
