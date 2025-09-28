"""Async Azure Monitor handler."""

import asyncio
import time
from typing import List, Dict, Any, Optional

from azure.monitor.ingestion import LogsIngestionClient
from azure.monitor.ingestion.aio import LogsIngestionClient as AsyncLogsIngestionClient
from azure.core.credentials import AzureKeyCredential

from ..types import LogRecord
from .async_base import AsyncBatchHandler

class AsyncAzureMonitorHandler(AsyncBatchHandler):
    """Async handler that sends logs to Azure Monitor."""
    
    def __init__(
        self,
        dcr_endpoint: str,
        dcr_immutable_id: str,
        dcr_stream_name: str,
        api_key: str,
        batch_size: int = 100,
        flush_interval: float = 5.0,
        max_queue_size: int = 10000,
        worker_count: int = 1,
        **kwargs: Any
    ):
        """Initialize the async Azure Monitor handler.
        
        Args:
            dcr_endpoint: Data Collection Rule endpoint
            dcr_immutable_id: DCR immutable ID
            dcr_stream_name: DCR stream name
            api_key: Azure Monitor API key
            batch_size: Maximum records per batch
            flush_interval: Maximum seconds between flushes
            max_queue_size: Maximum queue size
            worker_count: Number of worker threads
        """
        super().__init__(
            batch_size=batch_size,
            flush_interval=flush_interval,
            max_queue_size=max_queue_size,
            worker_count=worker_count
        )
        
        self.dcr_endpoint = dcr_endpoint
        self.dcr_immutable_id = dcr_immutable_id
        self.dcr_stream_name = dcr_stream_name
        self.credentials = AzureKeyCredential(api_key)
        
    def _format_event(self, record: LogRecord) -> Dict[str, Any]:
        """Format a log record as an Azure Monitor event."""
        return {
            'TimeGenerated': record.timestamp,
            'RawData': record.format_message(),
            'Level': record.level,
            'LoggerName': record.logger_name,
            'ThreadId': record.thread_id,
            'ProcessId': record.process_id,
            'Context': record.context
        }
        
    async def process_batch(self, batch: List[LogRecord]) -> None:
        """Process a batch of records asynchronously."""
        if not batch:
            return
            
        # Format events
        log_events = [self._format_event(record) for record in batch]
        
        # Create async client
        client = AsyncLogsIngestionClient(
            endpoint=self.dcr_endpoint,
            credential=self.credentials
        )
        
        # Send logs with retry
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                await client.upload(
                    rule_id=self.dcr_immutable_id,
                    stream_name=self.dcr_stream_name,
                    logs=log_events
                )
                break
                
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise
                    
                await asyncio.sleep(2 ** retry_count)