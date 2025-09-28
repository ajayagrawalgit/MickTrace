"""Google Cloud Stackdriver handler for MickTrace."""

import threading
import time
from typing import Any, Dict, List, Optional
from ..types import LogRecord

try:
    from google.cloud import logging
    from google.cloud.logging_v2.types import LogEntry
except ImportError:
    logging = None

class StackdriverHandler:
    """Handler for sending logs to Google Cloud Stackdriver."""
    
    def __init__(
        self,
        project_id: str,
        log_name: str = "micktrace",
        resource: Optional[Dict[str, Any]] = None,
        batch_size: int = 100,
        flush_interval: float = 5.0,
        credentials_path: Optional[str] = None,
    ):
        """Initialize the Stackdriver handler.
        
        Args:
            project_id: Google Cloud project ID
            log_name: Name of the log to write to
            resource: Resource to associate with logs
            batch_size: Max number of logs to batch before sending
            flush_interval: Max seconds to wait before sending logs
            credentials_path: Optional path to service account credentials
        """
        if logging is None:
            raise ImportError(
                "The google-cloud-logging library is required to use the Stackdriver handler. "
                "Install it with: pip install google-cloud-logging"
            )
            
        self.project_id = project_id
        self.log_name = log_name
        self.resource = resource or {
            "type": "global",
            "labels": {}
        }
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # Initialize Google Cloud client
        client_kwargs = {}
        if credentials_path:
            client_kwargs['credentials_file'] = credentials_path
            
        self.client = logging.Client(
            project=project_id,
            **client_kwargs
        )
        self.logger = self.client.logger(log_name)
        
        # Setup batching
        self._buffer: List[Dict[str, Any]] = []
        self._buffer_lock = threading.Lock()
        self._last_flush = time.time()
        
        # Start background flush thread
        self._flush_thread = threading.Thread(
            target=self._background_flush,
            daemon=True
        )
        self._flush_thread.start()
        
    def _severity_from_level(self, level: str) -> str:
        """Convert MickTrace level to Stackdriver severity."""
        severity_map = {
            "DEBUG": "DEBUG",
            "INFO": "INFO",
            "WARNING": "WARNING",
            "ERROR": "ERROR",
            "CRITICAL": "CRITICAL"
        }
        return severity_map.get(level, "DEFAULT")
        
    def emit(self, record: LogRecord) -> None:
        """Add a log record to the buffer."""
        entry = {
            'timestamp': record.timestamp,
            'severity': self._severity_from_level(record.level),
            'message': record.message,
            'resource': self.resource,
            'labels': {}
        }
        
        # Add context data as labels or jsonPayload
        if record.data:
            # Extract known Stackdriver fields
            trace = record.data.pop('trace', None)
            if trace:
                entry['trace'] = trace
                
            span_id = record.data.pop('span_id', None)
            if span_id:
                entry['span_id'] = span_id
                
            # Add remaining fields to jsonPayload
            entry['json_payload'] = record.data
            
        with self._buffer_lock:
            self._buffer.append(entry)
            
            # Check if we should flush
            if (len(self._buffer) >= self.batch_size or
                time.time() - self._last_flush >= self.flush_interval):
                self.flush()
                
    def flush(self) -> None:
        """Flush buffered logs to Stackdriver."""
        with self._buffer_lock:
            if not self._buffer:
                return
                
            try:
                # Convert to LogEntry objects
                entries = [
                    LogEntry(
                        timestamp=entry['timestamp'],
                        severity=entry['severity'],
                        text_payload=entry['message'],
                        resource=entry['resource'],
                        labels=entry['labels'],
                        trace=entry.get('trace'),
                        span_id=entry.get('span_id'),
                        json_payload=entry.get('json_payload')
                    )
                    for entry in self._buffer
                ]
                
                # Write entries in batch
                self.logger.write_entries(entries)
                
            except Exception as e:
                print(f"Error sending logs to Stackdriver: {e}")
                # Could implement retry logic here
                
            self._buffer.clear()
            self._last_flush = time.time()
            
    def _background_flush(self) -> None:
        """Background thread that periodically flushes logs."""
        while True:
            time.sleep(self.flush_interval)
            self.flush()