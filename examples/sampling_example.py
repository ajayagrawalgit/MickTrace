"""Example demonstrating MickTrace's smart sampling features."""

import asyncio
import random
import time
from micktrace import Logger
from micktrace.filters.sampling import SmartSampler, SamplingRule

# Create a logger
logger = Logger("sampling_example")

# Create and configure sampler
sampler = SmartSampler()

# Add sampling rules
sampler.add_rule(
    SamplingRule(
        name="debug_logs",
        rate=0.1,  # Sample 10% of debug logs
        condition=lambda r: r.level == "DEBUG",
        adaptive=True  # Increase sampling if errors increase
    )
)

sampler.add_rule(
    SamplingRule(
        name="info_logs",
        rate=0.5,  # Sample 50% of info logs
        condition=lambda r: r.level == "INFO",
        adaptive=True
    )
)

sampler.add_rule(
    SamplingRule(
        name="slow_operations",
        rate=0.8,  # Sample 80% of slow operations
        condition=lambda r: (
            r.data 
            and isinstance(r.data.get("duration_ms"), (int, float))
            and r.data["duration_ms"] > 100
        ),
        adaptive=True
    )
)

async def simulate_requests(num_requests: int):
    """Simulate a series of API requests with varying error rates."""
    error_probability = 0.1  # Start with 10% error rate
    
    for i in range(num_requests):
        # Generate correlation ID for request tracking
        correlation_id = f"req-{i}"
        
        # Set context and log request start
        logger.debug(
            "Processing request", 
            correlation_id=correlation_id,
            endpoint="/api/data"
        )
        
        # Simulate processing time
        duration = random.uniform(50, 200)
        await asyncio.sleep(duration / 1000)  # Convert to seconds
        
        # Log performance metrics
        logger.info(
            "Request processed",
            correlation_id=correlation_id,
            duration_ms=duration,
            endpoint="/api/data"
        )
        
        # Simulate errors with increasing probability
        if i > num_requests / 2:
            error_probability = 0.3  # Increase error rate halfway through
            
        if random.random() < error_probability:
            try:
                raise ValueError("Simulated error")
            except Exception as e:
                logger.error(
                    "Request failed",
                    correlation_id=correlation_id,
                    error=str(e),
                    duration_ms=duration
                )
        else:
            # Log successful completion
            logger.info(
                "Request completed successfully",
                correlation_id=correlation_id,
                duration_ms=duration
            )
            
        # Log debug information
        logger.debug(
            "Request cleanup",
            correlation_id=correlation_id,
            cache_cleared=True,
            temp_files_removed=2
        )

async def main():
    # Attach sampler to logger
    logger.add_filter(sampler)
    
    logger.info("Starting sampling demonstration")
    
    # Run simulation
    await simulate_requests(50)
    
    logger.info("Sampling demonstration completed")

if __name__ == "__main__":
    asyncio.run(main())