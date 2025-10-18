"""
MickTrace Buffering Example - Production Ready
==============================================

This example demonstrates buffering and batching patterns with MickTrace.
Shows how to handle high-volume logging efficiently.
"""

import asyncio
import random
import time
import micktrace
from pathlib import Path


class SimpleBuffer:
    """Simple in-memory buffer for demonstration."""

    def __init__(self, max_size=100, flush_interval=5.0):
        self.max_size = max_size
        self.flush_interval = flush_interval
        self.buffer = []
        self.last_flush = time.time()

    def add(self, message):
        """Add message to buffer."""
        self.buffer.append({"timestamp": time.time(), "message": message})

        # Auto-flush if buffer is full or time interval exceeded
        if (
            len(self.buffer) >= self.max_size
            or time.time() - self.last_flush >= self.flush_interval
        ):
            self.flush()

    def flush(self):
        """Flush buffer contents."""
        if self.buffer:
            print(f"📦 Flushing {len(self.buffer)} buffered messages")
            self.buffer.clear()
            self.last_flush = time.time()


def simulate_high_volume_logging():
    """Simulate high-volume logging with buffering."""
    print("=== High Volume Logging with Buffering ===")

    # Configure file logging
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    micktrace.configure(
        level="INFO",
        format="structured",
        handlers=[
            {
                "type": "file",
                "level": "INFO",
                "config": {"path": "logs/buffered_example.log"},
            }
        ],
    )

    logger = micktrace.get_logger("high_volume").bind(
        component="api_server", version="1.0.0"
    )

    # Create buffer for demonstration
    buffer = SimpleBuffer(max_size=50, flush_interval=2.0)

    # Simulate high-volume API requests
    request_types = ["GET", "POST", "PUT", "DELETE"]
    endpoints = ["/api/users", "/api/orders",
                 "/api/products", "/api/analytics"]

    print("🚀 Generating high-volume logs...")

    for i in range(200):  # Generate 200 log entries
        # Simulate API request
        method = random.choice(request_types)
        endpoint = random.choice(endpoints)
        status_code = random.choices(
            [200, 201, 400, 404, 500], weights=[70, 10, 10, 5, 5]
        )[0]
        response_time = random.uniform(10, 500)

        # Log to both file and buffer
        logger.info(
            "API request processed",
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            response_time_ms=round(response_time, 2),
            request_id=f"REQ-{i+1:04d}",
        )

        # Add to buffer for batch processing
        buffer.add(
            f"{method} {endpoint} - {status_code} ({response_time:.1f}ms)")

        # Small delay to simulate real traffic
        if i % 20 == 0:
            time.sleep(0.1)

    # Final flush
    buffer.flush()

    print("✅ High volume logging simulation completed!")
    print(f"📄 Logs written to logs/buffered_example.log")


def simulate_batch_processing():
    """Simulate batch processing with periodic logging."""
    print("\n=== Batch Processing with Periodic Logging ===")

    batch_logger = micktrace.get_logger("batch_processor").bind(
        component="data_processor", batch_type="user_analytics"
    )

    # Process data in batches
    total_records = 1000
    batch_size = 50
    processed_records = 0

    batch_logger.info(
        "Starting batch processing",
        total_records=total_records,
        batch_size=batch_size,
        estimated_batches=total_records // batch_size,
    )

    for batch_num in range(0, total_records, batch_size):
        batch_start = time.time()

        # Simulate batch processing
        current_batch_size = min(batch_size, total_records - batch_num)

        # Log batch start
        batch_logger.debug(
            "Processing batch",
            batch_number=batch_num // batch_size + 1,
            batch_size=current_batch_size,
            records_processed=processed_records,
        )

        # Simulate processing time
        processing_time = random.uniform(0.1, 0.3)
        time.sleep(processing_time)

        processed_records += current_batch_size
        batch_duration = time.time() - batch_start

        # Log batch completion
        batch_logger.info(
            "Batch completed",
            batch_number=batch_num // batch_size + 1,
            records_in_batch=current_batch_size,
            total_processed=processed_records,
            batch_duration_ms=round(batch_duration * 1000, 2),
            throughput_records_per_sec=round(
                current_batch_size / batch_duration, 2),
        )

        # Log progress every 5 batches
        if (batch_num // batch_size + 1) % 5 == 0:
            progress_pct = (processed_records / total_records) * 100
            batch_logger.info(
                "Processing progress",
                progress_percentage=round(progress_pct, 1),
                records_processed=processed_records,
                records_remaining=total_records - processed_records,
            )

    # Log final completion
    batch_logger.info(
        "Batch processing completed",
        total_records_processed=processed_records,
        total_batches=total_records // batch_size,
        status="success",
    )

    print("✅ Batch processing simulation completed!")


async def simulate_async_buffering():
    """Simulate async buffering patterns."""
    print("\n=== Async Buffering Patterns ===")

    async_logger = micktrace.get_logger("async_buffer").bind(
        component="async_processor", worker_pool="default"
    )

    # Simulate async message queue processing
    async def process_message(message_id: int, priority: str):
        """Process a single message asynchronously."""
        msg_logger = async_logger.bind(
            message_id=f"MSG-{message_id:04d}", priority=priority
        )

        # Simulate processing time based on priority
        if priority == "high":
            processing_time = random.uniform(0.01, 0.05)
        elif priority == "medium":
            processing_time = random.uniform(0.05, 0.15)
        else:  # low
            processing_time = random.uniform(0.15, 0.30)

        await asyncio.sleep(processing_time)

        msg_logger.info(
            "Message processed",
            processing_time_ms=round(processing_time * 1000, 2),
            status="completed",
        )

        return f"Processed-{message_id}"

    # Create messages with different priorities
    messages = []
    priorities = ["high", "medium", "low"]

    for i in range(30):
        priority = random.choice(priorities)
        messages.append((i + 1, priority))

    async_logger.info(
        "Starting async message processing",
        total_messages=len(messages),
        priority_distribution={
            "high": len([m for m in messages if m[1] == "high"]),
            "medium": len([m for m in messages if m[1] == "medium"]),
            "low": len([m for m in messages if m[1] == "low"]),
        },
    )

    # Process messages in batches of 10
    batch_size = 10
    for i in range(0, len(messages), batch_size):
        batch = messages[i: i + batch_size]

        async_logger.info(
            "Processing message batch",
            batch_number=i // batch_size + 1,
            batch_size=len(batch),
        )

        # Process batch concurrently
        tasks = [process_message(msg_id, priority)
                 for msg_id, priority in batch]
        results = await asyncio.gather(*tasks)

        async_logger.info(
            "Message batch completed",
            batch_number=i // batch_size + 1,
            messages_processed=len(results),
        )

    async_logger.info(
        "All async message processing completed", total_messages=len(messages)
    )

    print("✅ Async buffering simulation completed!")


def main():
    """Main function demonstrating buffering patterns."""
    print("🚀 MickTrace Buffering Example")
    print("=" * 45)

    # Run synchronous examples
    simulate_high_volume_logging()
    simulate_batch_processing()

    # Run async example
    asyncio.run(simulate_async_buffering())

    print("\n🎉 All buffering examples completed successfully!")
    print("💡 Buffering helps manage high-volume logging efficiently")


if __name__ == "__main__":
    main()
