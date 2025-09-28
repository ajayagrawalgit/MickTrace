"""Example demonstrating async handlers in micktrace."""

import asyncio
import time
from micktrace import Logger, Context, ConsoleHandler
from micktrace.handlers import (
    AsyncCloudWatchHandler,
    AsyncGoogleCloudHandler,
    AsyncAzureMonitorHandler
)

# Initialize handlers
console_handler = ConsoleHandler()

cloudwatch_handler = AsyncCloudWatchHandler(
    log_group="/my-app/logs",
    log_stream="example",
    # AWS credentials can be configured via environment variables or AWS CLI
)

google_handler = AsyncGoogleCloudHandler(
    project_id="my-project",
    log_name="my-app-logs",
    resource_type="global",
    # Google Cloud credentials can be set via GOOGLE_APPLICATION_CREDENTIALS
)

azure_handler = AsyncAzureMonitorHandler(
    dcr_endpoint="https://my-dcr-endpoint",
    dcr_immutable_id="my-dcr-id",
    dcr_stream_name="my-stream",
    api_key="my-api-key"
)

# Create logger with multiple handlers
logger = Logger(
    name="example",
    handlers=[
        console_handler,
        cloudwatch_handler,
        google_handler,
        azure_handler
    ]
)

async def main():
    """Run example demonstrating async handlers."""
    # Create some context
    with Context(
        service="example-service",
        environment="development",
        version="1.0.0"
    ):
        # Log some messages that will be batched and sent async
        for i in range(1000):
            logger.info(
                "Example log message",
                count=i,
                timestamp=time.time()
            )
            
            if i % 100 == 0:
                logger.error(
                    "Example error message",
                    error_code=500,
                    count=i
                )
                
            # Small delay to simulate real work
            await asyncio.sleep(0.01)
            
    # Ensure all handlers flush before exiting
    logger.flush()
    
if __name__ == "__main__":
    asyncio.run(main())