"""Example demonstrating advanced buffering and aggregation."""

import time
import random
from micktrace import Logger, Context
from micktrace.handlers import BufferedHandler

def alert_on_errors(records):
    """Alert callback for error aggregation."""
    print(f"Alert: {len(records)} errors in the last minute!")
    for record in records:
        print(f"  Error: {record.message}")

def alert_on_latency(records):
    """Alert callback for high latency."""
    latencies = [r.latency for r in records if hasattr(r, 'latency')]
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        print(f"Alert: Average latency {avg_latency:.2f}ms over threshold!")
        print(f"  Affected requests: {len(records)}")

# Create buffered handler with callbacks
handler = BufferedHandler(
    max_buffer_size=1000000,  # 1M records
    compression_enabled=True,  # Enable compression
    max_window=3600.0,  # 1 hour window
    callback=lambda records: print(f"Flushed {len(records)} records")
)

# Add aggregation rules
handler.add_aggregation_rule(
    field="level",
    window=60.0,  # 1 minute window
    threshold=10,  # Alert on 10+ errors
    callback=alert_on_errors
)

handler.add_aggregation_rule(
    field="latency",
    window=300.0,  # 5 minute window
    threshold=100,  # Alert on 100+ slow requests
    callback=alert_on_latency
)

# Create logger
logger = Logger("buffer-example")
logger.add_handler(handler)

def simulate_requests():
    """Simulate a mix of requests with varying latencies."""
    endpoints = ['/api/users', '/api/posts', '/api/comments']
    
    for i in range(1000):
        # Simulate request context
        with Context(
            service="api-server",
            endpoint=random.choice(endpoints),
            request_id=f"req-{i}"
        ):
            # Simulate latency
            latency = random.lognormvariate(2, 0.5)  # Log-normal distribution
            
            # Log request
            logger.info(
                "API request processed",
                latency=latency,
                status=200 if latency < 100 else 500
            )
            
            # Sometimes log errors
            if latency > 100:
                logger.error(
                    "Request timed out",
                    latency=latency,
                    error_code="TIMEOUT"
                )
                
            # Add some warnings
            if 50 < latency < 100:
                logger.warning(
                    "High latency detected",
                    latency=latency
                )
                
            # Small delay between requests
            time.sleep(0.01)
            
def print_metrics():
    """Print current metrics."""
    metrics = handler.get_metrics()
    
    print("\nAggregation Metrics:")
    for group, m in metrics.items():
        print(f"\n{group}:")
        print(f"  Total Count: {m.count}")
        print(f"  Error Count: {m.error_count}")
        print(f"  Warning Count: {m.warning_count}")
        print(f"  Avg Latency: {m.avg_latency:.2f}ms")
        print(f"  Unique Contexts: {len(m.unique_contexts)}")
        
if __name__ == "__main__":
    try:
        simulate_requests()
    finally:
        print_metrics()
        handler.shutdown()