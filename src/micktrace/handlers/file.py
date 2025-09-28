"""File handlers for micktrace."""

import os
import queue
from typing import Any, Optional, Callable
from threading import Thread, Event
from ..types import LogRecord
import json


import traceback

class FileHandler:
    def __init__(
        self,
        filename: str,
        max_bytes: int = 10485760,  # 10MB default
        backup_count: int = 5,
        async_mode: bool = False,
        **kwargs: Any
    ) -> None:
        """Initialize FileHandler.
        
        Args:
            filename: Path to the log file (required)
            max_bytes: Maximum size in bytes before rotation
            backup_count: Number of backup files to keep
            async_mode: Whether to use asynchronous logging
        """
        if not filename:
            raise ValueError("filename must be provided")
        
        self.filename = os.path.abspath(filename)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.config = kwargs
        
        try:
            # Ensure directory exists
            log_dir = os.path.dirname(self.filename)
            if log_dir:  # Only create if path has a directory component
                os.makedirs(log_dir, exist_ok=True)
                
            # Verify we can write to the file
            with open(self.filename, 'a') as f:
                f.write("")
        except Exception as e:
            raise IOError(f"Cannot initialize log file {self.filename}: {str(e)}") from e
        
        # Setup async queue and worker if async mode is enabled
        self.async_mode = async_mode
        if self.async_mode:
            self.queue = queue.Queue()
            self.stop_event = Event()
            self.worker = Thread(target=self._worker)
            self.worker.daemon = True
            self.worker.start()

    def should_rotate(self) -> bool:
        """Check if the log file needs to be rotated."""
        try:
            if not os.path.exists(self.filename):
                return False
            return os.path.getsize(self.filename) >= self.max_bytes
        except Exception:
            return False

    def rotate(self) -> None:
        """Rotate the log files."""
        if not os.path.exists(self.filename):
            return

        for i in range(self.backup_count - 1, 0, -1):
            source = f"{self.filename}.{i}"
            dest = f"{self.filename}.{i + 1}"
            if os.path.exists(source):
                try:
                    if os.path.exists(dest):
                        os.remove(dest)
                    os.rename(source, dest)
                except Exception:
                    pass

        try:
            if os.path.exists(self.filename):
                os.rename(self.filename, f"{self.filename}.1")
        except Exception:
            pass

    def _write(self, record: LogRecord) -> None:
        """Write a log record to file."""
        try:
            if self.should_rotate():
                self.rotate()

            # Convert record to JSON for consistent storage
            log_data = {
                "timestamp": str(record.timestamp),
                "level": record.level,
                "message": record.message,
                "logger_name": record.logger_name,
                "data": record.data
            }
            
            log_line = json.dumps(log_data)
            
            # Write with atomic operation when possible
            temp_file = f"{self.filename}.tmp"
            try:
                # Append directly to the file
                with open(self.filename, "a", encoding="utf-8") as f:
                    f.write(log_line + "\n")
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
            except Exception as e:
                raise IOError(f"Failed to write to {self.filename}: {str(e)}") from e
        except Exception as e:
            raise IOError(f"Failed to process log record: {str(e)}") from e

    def emit(self, record: LogRecord) -> None:
        """Emit a log record.
        
        In async mode, puts the record in a queue.
        In sync mode, writes directly to file.
        """
        if self.async_mode:
            try:
                self.queue.put(record)
            except queue.Full:
                pass  # Silent failure if queue is full
        else:
            self._write(record)

    def handle(self, record: LogRecord) -> None:
        """Handle a log record."""
        try:
            # Check level if specified
            if hasattr(self, 'level'):
                from ..types import LogLevel
                record_level = LogLevel.from_string(record.level)
                handler_level = LogLevel.from_string(self.level)
                if record_level < handler_level:
                    return
                    
            self.emit(record)
        except Exception as e:
            # Log handler failures should not crash the application
            # but we should report them somehow - possibly through a callback
            pass

    def _worker(self) -> None:
        """Background worker for async mode."""
        while not self.stop_event.is_set():
            try:
                record = self.queue.get(timeout=0.1)
                self._write(record)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                continue

    def close(self) -> None:
        """Clean shutdown for async mode."""
        if self.async_mode:
            self.stop_event.set()
            self.worker.join()
            # Process any remaining items in the queue
            while not self.queue.empty():
                try:
                    record = self.queue.get_nowait()
                    self._write(record)
                    self.queue.task_done()
                except queue.Empty:
                    break