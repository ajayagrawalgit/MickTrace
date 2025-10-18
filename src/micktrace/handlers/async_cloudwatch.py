"""Async AWS CloudWatch Logs handler."""

import asyncio
import time
from typing import List, Dict, Any, Optional

import aioboto3
from botocore.config import Config

from ..types import LogRecord
from .async_base import AsyncBatchHandler


class AsyncCloudWatchHandler(AsyncBatchHandler):
    """Async handler that sends logs to AWS CloudWatch Logs."""

    def __init__(
        self,
        log_group: str,
        log_stream: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_profile: Optional[str] = None,
        batch_size: int = 100,
        flush_interval: float = 5.0,
        max_queue_size: int = 10000,
        worker_count: int = 1,
        **kwargs: Any,
    ):
        """Initialize the async CloudWatch handler.

        Args:
            log_group: The CloudWatch log group name
            log_stream: Optional log stream name (default: auto-generated)
            aws_access_key_id: Optional AWS access key
            aws_secret_access_key: Optional AWS secret key
            aws_region: Optional AWS region
            aws_profile: Optional AWS credential profile
            batch_size: Maximum records per batch
            flush_interval: Maximum seconds between flushes
            max_queue_size: Maximum queue size
            worker_count: Number of worker threads
        """
        super().__init__(
            batch_size=batch_size,
            flush_interval=flush_interval,
            max_queue_size=max_queue_size,
            worker_count=worker_count,
        )

        self.log_group = log_group
        self.log_stream = log_stream or f"micktrace-{int(time.time())}"

        # AWS credentials
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region
        self.aws_profile = aws_profile

        # Boto3 config
        self.boto_config = Config(
            retries=dict(max_attempts=5, mode="adaptive"), **kwargs
        )

        # CloudWatch sequence token
        self._sequence_token: Optional[str] = None

    async def _get_logs_client(self):
        """Get an async CloudWatch Logs client."""
        session = aioboto3.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region,
            profile_name=self.aws_profile,
        )
        return session.client("logs", config=self.boto_config)

    async def _ensure_log_group_exists(self, client) -> None:
        """Ensure the log group exists."""
        try:
            await client.create_log_group(logGroupName=self.log_group)
        except client.exceptions.ResourceAlreadyExistsException:
            pass

    async def _ensure_log_stream_exists(self, client) -> None:
        """Ensure the log stream exists and get sequence token."""
        try:
            await client.create_log_stream(
                logGroupName=self.log_group, logStreamName=self.log_stream
            )
        except client.exceptions.ResourceAlreadyExistsException:
            # Get existing sequence token
            response = await client.describe_log_streams(
                logGroupName=self.log_group,
                logStreamNamePrefix=self.log_stream,
                limit=1,
            )

            streams = response.get("logStreams", [])
            if streams:
                self._sequence_token = streams[0].get("uploadSequenceToken")

    def _format_event(self, record: LogRecord) -> Dict[str, Any]:
        """Format a log record as a CloudWatch event."""
        return {
            "timestamp": int(record.timestamp * 1000),
            "message": record.format_message(),
        }

    async def process_batch(self, batch: List[LogRecord]) -> None:
        """Process a batch of records asynchronously."""
        if not batch:
            return

        async with await self._get_logs_client() as client:
            # Ensure log group and stream exist
            await self._ensure_log_group_exists(client)
            await self._ensure_log_stream_exists(client)

            # Format events
            log_events = [self._format_event(record) for record in batch]

            # Send logs with retry
            max_retries = 5
            retry_count = 0

            while retry_count < max_retries:
                try:
                    kwargs = {
                        "logGroupName": self.log_group,
                        "logStreamName": self.log_stream,
                        "logEvents": log_events,
                    }

                    if self._sequence_token:
                        kwargs["sequenceToken"] = self._sequence_token

                    response = await client.put_log_events(**kwargs)
                    self._sequence_token = response.get("nextSequenceToken")
                    break

                except (
                    client.exceptions.InvalidSequenceTokenException,
                    client.exceptions.DataAlreadyAcceptedException,
                ) as e:
                    # Update sequence token and retry
                    if hasattr(e, "response"):
                        self._sequence_token = e.response.get(
                            "expectedSequenceToken")
                    retry_count += 1
                    await asyncio.sleep(2**retry_count)

                except Exception as e:
                    raise
