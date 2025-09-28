"""Azure Monitor handler for MickTrace."""

import threading
import time
from typing import Any, Dict, List, Optional, Union
from ..types import LogRecord

try:
    from opencensus.ext.azure.log_exporter import AzureLogHandler
except ImportError:
    AzureLogHandler = None

class AzureMonitorHandler:
    """Handler for sending logs to Azure Monitor."""
    
    def __init__(
        self,
        connection_string: str,
        custom_dimensions: Optional[Dict[str, str]] = None,
        batch_size: int = 100,
        flush_interval: float = 5.0
    ):
        """Initialize the Azure Monitor handler.
        
            connection_string: Azure Monitor connection string or instrumentation key
            custom_dimensions: Default custom dimensions to add to all logs
            batch_size: Max number of logs to batch before sending
            flush_interval: Max seconds to wait before sending logs
        """
        if AzureLogHandler is None:
            raise ImportError(
                "Azure Monitor integration requires additional dependencies. "
                "Install with: pip install micktrace[azure]"
            )
            
        # If connection string is just an instrumentation key, convert to proper format
        if not connection_string.startswith("InstrumentationKey="):
            connection_string = f"InstrumentationKey={connection_string}"
        self.custom_dimensions = custom_dimensions or {}
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # Initialize Azure Monitor client
        self.handler = AzureLogHandler(
            connection_string=connection_string
        )
        
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
        
    def _convert_level(self, level: str) -> int:
        """Convert MickTrace level to Azure Monitor severity level."""
        level_map = {
            "DEBUG": 1,    # Verbose
            "INFO": 2,     # Information
            "WARNING": 3,  # Warning
            "ERROR": 4,    # Error
            "CRITICAL": 4  # Critical (same as Error in Azure)
        }
        return level_map.get(level, 1)
        
    def emit(self, record: LogRecord) -> None:
        """Add a log record to the buffer."""
        # Prepare custom dimensions
        dimensions = self.custom_dimensions.copy()
        
        # Add record data as custom dimensions
        if record.data:
            # Handle nested dictionaries
            def flatten_dict(d: Dict[str, Any], prefix: str = "") -> Dict[str, str]:
                items: List[tuple[str, str]] = []
                for k, v in d.items():
                    new_key = f"{prefix}{k}" if prefix else k
                    if isinstance(v, dict):
                        items.extend(flatten_dict(v, f"{new_key}_").items())
                    else:
                        items.append((new_key, str(v)))
                return dict(items)
            
            dimensions.update(flatten_dict(record.data))
            
        # Create Azure Monitor compatible log entry
        entry = {
            'name': "MickTrace",  # Event name
            'time': record.timestamp,
            'level': self._convert_level(record.level),
            'message': record.message,
            'custom_dimensions': dimensions
        }
        
        # Add exception data if present
        if record.exception:
            entry['custom_dimensions']['exception_type'] = record.exception.get('type')
            entry['custom_dimensions']['exception_message'] = record.exception.get('message')
            entry['custom_dimensions']['exception_stacktrace'] = record.exception.get('stacktrace')
            
        with self._buffer_lock:
            self._buffer.append(entry)
            
            # Check if we should flush
            if (len(self._buffer) >= self.batch_size or
                time.time() - self._last_flush >= self.flush_interval):
                self.flush()
                
    def flush(self) -> None:
        """Flush buffered logs to Azure Monitor."""
        with self._buffer_lock:
            if not self._buffer:
                return
                
            try:
                # Send each log entry through the Azure handler
                for entry in self._buffer:
                    self.handler.emit(
                        type(
                            "AzureLogRecord",
                            (),
                            {
                                'name': entry['name'],
                                'msg': entry['message'],
                                'levelno': entry['level'],
                                'created': entry['time'],
                                'custom_dimensions': entry['custom_dimensions']
                            }
                        )
                    )
                    
                # Force flush the Azure handler
                self.handler.flush()
                
            except Exception as e:
                # Could implement retry logic here
                pass
                
            self._buffer.clear()
            self._last_flush = time.time()
            
    def _background_flush(self) -> None:
        """Background thread that periodically flushes logs."""
        while True:
            time.sleep(self.flush_interval)
            self.flush()