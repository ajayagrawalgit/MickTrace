"""Example demonstrating MickTrace's performance monitoring features."""

import asyncio
import random
import time
from micktrace import Logger
from micktrace.utils.performance import Timer, track_memory

# Create a logger
logger = Logger("performance_example")

@Timer(logger, "process_batch")
def process_batch(items):
    """Process a batch of items with timing."""
    time.sleep(random.uniform(0.1, 0.5))  # Simulate work
    return [item * 2 for item in items]

@Timer(logger, "database_operation", threshold_ms=100)
async def database_operation(query):
    """Simulate a database operation that only logs if it takes >100ms."""
    await asyncio.sleep(random.uniform(0.05, 0.2))  # Simulate DB query
    return {"results": [1, 2, 3]}

@track_memory(logger, "memory_intensive_operation")
def memory_intensive_operation():
    """Demonstrate memory tracking."""
    # Create a large list to show memory impact
    large_list = list(range(1000000))
    time.sleep(0.1)  # Simulate work
    return sum(large_list)

async def nested_operations():
    """Demonstrate nested operation timing."""
    async with Timer(logger, "outer_operation"):
        # First nested operation
        with Timer(logger, "nested_1"):
            result1 = process_batch([1, 2, 3, 4, 5])
            
        # Second nested operation
        with Timer(logger, "nested_2"):
            result2 = await database_operation("SELECT * FROM table")
            
        # Third nested operation with custom context
        with Timer(logger, "nested_3", extra_context={"custom_field": "value"}):
            result3 = memory_intensive_operation()
            
        return result1, result2, result3

async def main():
    # Set up some permanent context
    logger.context.bind_permanent(
        environment="development",
        service_version="1.0.0"
    )
    
    try:
        # Run operations that will be timed
        logger.info("Starting performance test")
        
        # Run some basic operations
        process_batch([1, 2, 3])
        await database_operation("query")
        
        # Run nested operations to show operation path tracking
        await nested_operations()
        
        # Run an operation that fails to show error handling
        with Timer(logger, "failing_operation"):
            raise ValueError("Simulated error")
            
    except Exception as e:
        logger.error("Test failed", error=str(e))
    
    logger.info("Performance test completed")

if __name__ == "__main__":
    asyncio.run(main())