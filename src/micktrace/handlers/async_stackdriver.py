"""Async Google Cloud Logging handler."""

import asyncio
import time
from typing import List, Dict, Any, Optional

from google.cloud import logging_v2
from google.cloud.logging_v2.types import LogEntry

from ..types import LogRecord
from .async_base import AsyncBatchHandler

class AsyncGoogleCloudHandler(AsyncBatchHandler):
    """Async handler that sends logs to Google Cloud Logging."""
    
    def __init__(
        self,
        project_id: str,
        log_name: str,
        resource_type: str = "global",
        resource_labels: Optional[Dict[str, str]] = None,
        credentials_path: Optional[str] = None,
        batch_size: int = 100,
        flush_interval: float = 5.0,
        max_queue_size: int = 10000,
        worker_count: int = 1,
        **kwargs: Any
    ):
        """Initialize the async Google Cloud handler.
        
        Args:
            project_id: Google Cloud project ID
            log_name: Name of the log to write to
            resource_type: Google Cloud resource type
            resource_labels: Resource labels
            credentials_path: Optional path to service account key file
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
        
        self.project_id = project_id
        self.log_name = log_name
        self.resource_type = resource_type
        self.resource_labels = resource_labels or {}
        self.credentials_path = credentials_path
        
    def _format_event(self, record: LogRecord) -> Dict[str, Any]:
        """Format a log record as a Google Cloud log entry."""
        severity = {
            'DEBUG': 'DEBUG',
            'INFO': 'INFO',
            'WARNING': 'WARNING',
            'ERROR': 'ERROR',
            'CRITICAL': 'CRITICAL'
        }.get(record.level, 'DEFAULT')
        
        return {
            'severity': severity,
            'timestamp': {'seconds': int(record.timestamp)},
            'textPayload': record.format_message(),
            'labels': {
                'logger': record.logger_name,
                'thread_id': str(record.thread_id),
                'process_id': str(record.process_id)
            },
            'sourceLocation': {
                'file': record.file_path,
                'line': str(record.line_number),
                'function': record.function_name
            }
        }
        
    async def process_batch(self, batch: List[LogRecord]) -> None:
        """Process a batch of records asynchronously."""
        if not batch:
            return
            
        # Format entries
        entries = []
        for record in batch:
            entry = self._format_event(record)
            entry['logName'] = f"projects/{self.project_id}/logs/{self.log_name}"
            entry['resource'] = {
                'type': self.resource_type,
                'labels': self.resource_labels
            }
            entries.append(entry)
            
        # Create sync client but run in thread
        client = (
            logging_v2.Client.from_service_account_json(self.credentials_path)
            if self.credentials_path
            else logging_v2.Client()
        ).logging_api
        
        # Send logs with retry
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                client.write_entries(entries)
                break
                
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"Error sending logs to Google Cloud: {e}")
                    raise
                
                # Sleep in thread
                time.sleep(2 ** retry_count)
                time.sleep(2 ** retry_count)