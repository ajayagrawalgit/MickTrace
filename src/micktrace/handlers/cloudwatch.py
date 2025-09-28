"""AWS CloudWatch handler for MickTrace."""

import threading
import time
from typing import Any, Dict, List, Optional
from ..types import LogRecord

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None

class CloudWatchHandler:
    """Handler for sending logs to AWS CloudWatch Logs."""
    
    def __init__(
        self,
        log_group_name: str,
        log_stream_name: str,
        region: str = "us-west-2",
        batch_size: int = 100,
        flush_interval: float = 5.0,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ):
        """Initialize the CloudWatch handler.
        
        Args:
            log_group_name: The name of the CloudWatch Logs group
            log_stream_name: The name of the CloudWatch Logs stream
            region: AWS region (default: us-west-2)
            batch_size: Max number of logs to batch before sending
            flush_interval: Max seconds to wait before sending logs
            aws_access_key_id: Optional AWS access key
            aws_secret_access_key: Optional AWS secret key
        """
        if boto3 is None:
            raise ImportError(
                "The boto3 library is required to use the CloudWatch handler. "
                "Install it with: pip install boto3"
            )
            
        self.log_group_name = log_group_name
        self.log_stream_name = log_stream_name
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # Initialize AWS client
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region
        )
        self.client = session.client('logs')
        
        # Initialize sequence token
        self.sequence_token = self._get_sequence_token()
        
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
        
    def _get_sequence_token(self) -> Optional[str]:
        """Get the sequence token for the log stream."""
        try:
            # Try to create log group if it doesn't exist
            try:
                self.client.create_log_group(logGroupName=self.log_group_name)
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                    raise
                    
            # Try to create log stream if it doesn't exist
            try:
                self.client.create_log_stream(
                    logGroupName=self.log_group_name,
                    logStreamName=self.log_stream_name
                )
                return None  # New stream starts with no sequence token
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                    raise
                    
            # Get existing stream's sequence token
            response = self.client.describe_log_streams(
                logGroupName=self.log_group_name,
                logStreamNamePrefix=self.log_stream_name,
                limit=1
            )
            
            streams = response.get('logStreams', [])
            if streams and streams[0]['logStreamName'] == self.log_stream_name:
                return streams[0].get('uploadSequenceToken')
                
            return None
            
        except Exception as e:
            print(f"Error getting sequence token: {e}")
            return None
            
    def emit(self, record: LogRecord) -> None:
        """Add a log record to the buffer."""
        log_entry = {
            'timestamp': int(record.timestamp * 1000),
            'message': record.message
        }
        
        # Add context data as structured fields
        if record.data:
            log_entry.update(record.data)
            
        with self._buffer_lock:
            self._buffer.append(log_entry)
            
            # Check if we should flush
            if (len(self._buffer) >= self.batch_size or
                time.time() - self._last_flush >= self.flush_interval):
                self.flush()
                
    def flush(self) -> None:
        """Flush buffered logs to CloudWatch."""
        with self._buffer_lock:
            if not self._buffer:
                return
                
            log_events = [{
                'timestamp': entry['timestamp'],
                'message': str(entry)  # Convert dict to string for CloudWatch
            } for entry in self._buffer]
            
            try:
                kwargs = {
                    'logGroupName': self.log_group_name,
                    'logStreamName': self.log_stream_name,
                    'logEvents': log_events
                }
                
                if self.sequence_token:
                    kwargs['sequenceToken'] = self.sequence_token
                    
                response = self.client.put_log_events(**kwargs)
                self.sequence_token = response.get('nextSequenceToken')
                
            except Exception as e:
                print(f"Error sending logs to CloudWatch: {e}")
                # Could implement retry logic here
                
            self._buffer.clear()
            self._last_flush = time.time()
            
    def _background_flush(self) -> None:
        """Background thread that periodically flushes logs."""
        while True:
            time.sleep(self.flush_interval)
            self.flush()