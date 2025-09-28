"""Example of using MickTrace's advanced context features."""

import asyncio
import os
import psutil
import time
from micktrace import Logger

# Create a logger
logger = Logger("context_example")

# System metrics provider
def get_system_metrics():
    process = psutil.Process(os.getpid())
    return {
        "cpu_percent": process.cpu_percent(),
        "memory_usage": process.memory_info().rss / 1024 / 1024,  # MB
        "thread_count": process.num_threads(),
        "open_files": len(process.open_files())
    }

# Example of request context
def handle_request(request_id: str, user_id: str):
    # Add request context
    with logger.context.bind(request_id=request_id, user_id=user_id):
        logger.info("Processing request", operation="start")
        
        # Add nested context for a specific operation
        with logger.context.bind(operation={
            "name": "data_validation",
            "stage": "input",
            "timestamp": time.time()
        }):
            logger.info("Validating input data")
            # ... validation code ...
            
        # Context from previous bind is automatically removed
        logger.info("Input validation complete")
        
        # Add another nested context
        with logger.context.bind(operation={
            "name": "data_processing",
            "stage": "compute",
            "timestamp": time.time()
        }):
            logger.info("Processing data")
            # ... processing code ...
            
        logger.info("Request completed")

async def main():
    # Add system metrics provider that refreshes every 5 seconds
    logger.context.add_provider("system", get_system_metrics, refresh_interval=5.0)
    
    # Add some permanent context
    logger.context.bind_permanent(
        environment="development",
        service_version="1.0.0"
    )
    
    # Simulate some requests
    for i in range(3):
        handle_request(f"req_{i}", f"user_{i}")
        await asyncio.sleep(2)  # Wait to see system metrics change
        
    # Clean up
    logger.context.remove_provider("system")

if __name__ == "__main__":
    asyncio.run(main())