"""Example of using MickTrace's cloud integrations."""

import asyncio
from datetime import datetime
from micktrace import Logger

# Initialize loggers for different cloud platforms
aws_logger = Logger("aws_example", config={
    "handlers": {
        "cloudwatch": {
            "type": "CloudWatchHandler",
            "log_group_name": "my-application",
            "log_stream_name": "service-logs",
            "region": "us-west-2",
            "batch_size": 100,
            "flush_interval": 5.0
        }
    }
})

gcp_logger = Logger("gcp_example", config={
    "handlers": {
        "stackdriver": {
            "type": "StackdriverHandler",
            "project_id": "my-project",
            "resource": {
                "type": "gce_instance",
                "labels": {
                    "instance_id": "my-instance",
                    "zone": "us-central1-a"
                }
            }
        }
    }
})

azure_logger = Logger("azure_example", config={
    "handlers": {
        "azure": {
            "type": "AzureMonitorHandler",
            "connection_string": "InstrumentationKey=YOUR_KEY",
            "custom_dimensions": {
                "service": "backend-api",
                "environment": "production"
            }
        }
    }
})

async def simulate_logs():
    # Simulate various log events with rich context
    for i in range(5):
        # AWS CloudWatch example with structured data
        aws_logger.info(
            "API request processed",
            latency_ms=random.randint(10, 500),
            endpoint="/api/users",
            method="GET",
            status_code=200,
            request_id=f"req-{i}"
        )

        # GCP Stackdriver example with error reporting
        try:
            if i % 2 == 0:
                raise ValueError("Simulated error")
        except Exception as e:
            gcp_logger.error(
                "Error processing request",
                error=str(e),
                severity="ERROR",
                component="user-service",
                trace_id=f"trace-{i}"
            )

        # Azure Monitor example with metrics
        azure_logger.info(
            "Transaction completed",
            properties={
                "transaction_id": f"tx-{i}",
                "user_id": f"user-{i}",
                "amount": random.uniform(10, 1000)
            },
            measurements={
                "processing_time": random.uniform(0.1, 2.0),
                "memory_usage": random.uniform(100, 500)
            }
        )

        await asyncio.sleep(1)

async def main():
    await simulate_logs()
    
    # Ensure all logs are flushed
    aws_logger.flush()
    gcp_logger.flush()
    azure_logger.flush()

if __name__ == "__main__":
    asyncio.run(main())