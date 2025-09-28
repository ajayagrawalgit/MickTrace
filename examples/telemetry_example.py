"""Example demonstrating MickTrace's OpenTelemetry integration."""

import asyncio
import random
import time
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from micktrace import Logger
from micktrace.formatters.opentelemetry import OpenTelemetryFormatter

# Initialize OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("micktrace.example")

# Configure exporter
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(ConsoleSpanExporter())
)

# Create logger with OpenTelemetry formatter
logger = Logger("telemetry_example", config={
    "handlers": {
        "console": {
            "type": "console",
            "formatter": {
                "type": "OpenTelemetryFormatter"
            }
        }
    }
})

async def process_item(item_id: int) -> dict:
    """Process a single item with tracing."""
    with tracer.start_as_current_span("process_item") as span:
        # Add attributes to span
        span.set_attributes({
            "item.id": item_id,
            "processor.name": "example"
        })
        
        logger.info(
            f"Processing item {item_id}",
            item_id=item_id,
            processor="example"
        )
        
        # Simulate work
        duration = random.uniform(0.1, 0.5)
        await asyncio.sleep(duration)
        
        # Simulate occasional errors
        if random.random() < 0.2:  # 20% error rate
            try:
                raise ValueError(f"Failed to process item {item_id}")
            except Exception as e:
                logger.error(
                    "Item processing failed",
                    item_id=item_id,
                    duration_ms=duration * 1000,
                    error=str(e)
                )
                span.set_status(Status(StatusCode.ERROR))
                span.record_exception(e)
                raise
                
        result = {
            "item_id": item_id,
            "duration_ms": duration * 1000,
            "status": "completed"
        }
        
        logger.info(
            "Item processing completed",
            **result
        )
        
        return result

async def process_batch(batch_id: int, items: list[int]) -> None:
    """Process a batch of items with tracing."""
    with tracer.start_as_current_span("process_batch") as span:
        span.set_attributes({
            "batch.id": batch_id,
            "batch.size": len(items)
        })
        
        logger.info(
            f"Processing batch {batch_id}",
            batch_id=batch_id,
            item_count=len(items)
        )
        
        try:
            # Process items concurrently
            tasks = [process_item(item) for item in items]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successes and failures
            successes = sum(1 for r in results if not isinstance(r, Exception))
            failures = sum(1 for r in results if isinstance(r, Exception))
            
            logger.info(
                "Batch processing completed",
                batch_id=batch_id,
                successes=successes,
                failures=failures
            )
            
            if failures > 0:
                span.set_status(Status(StatusCode.ERROR))
                
        except Exception as e:
            logger.error(
                "Batch processing failed",
                batch_id=batch_id,
                error=str(e)
            )
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception(e)
            raise

async def main():
    """Run the example."""
    logger.info("Starting OpenTelemetry integration example")
    
    try:
        with tracer.start_as_current_span("main"):
            # Process multiple batches
            for batch_id in range(3):
                items = list(range(batch_id * 5, (batch_id + 1) * 5))
                try:
                    await process_batch(batch_id, items)
                except Exception as e:
                    logger.error(
                        "Main loop error",
                        batch_id=batch_id,
                        error=str(e)
                    )
                    
    except Exception as e:
        logger.error("Example failed", error=str(e))
    finally:
        logger.info("OpenTelemetry integration example completed")

if __name__ == "__main__":
    asyncio.run(main())