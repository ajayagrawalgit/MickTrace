"""File handlers for micktrace."""

import os
import queue
from typing import Any, Optional, Callable
from threading import Thread, Event
from ..types import LogRecord
import json


class FileHandler:
    def __init__(
        self,
        name: str = "file",
        filename: str = "app.log",
        max_bytes: int = 10485760,  # 10MB default
        backup_count: int = 5,
        **kwargs: Any
    ) -> None:
        """Initialize FileHandler.
        
        Args:
            name: Name of the handler
            filename: Path to the log file
            max_bytes: Maximum size in bytes before rotation
            backup_count: Number of backup files to keep
        """
        self.name = name
        self.filename = filename
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.config = kwargs
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        
        # Setup async queue and worker if async mode is enabled
        self.async_mode = kwargs.get("async_mode", False)
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

            # Get absolute path
            abs_filename = os.path.abspath(self.filename)
            print(f"DEBUG FileHandler: Writing record to {abs_filename}")
            
            # Convert record to JSON for consistent storage
            log_data = {
                "timestamp": str(record.timestamp),
                "level": record.level,
                "message": record.message,
                "logger_name": record.logger_name,
                "data": record.data
            }
            
            log_line = json.dumps(log_data)
            print(f"DEBUG FileHandler: Preparing to write: {log_line}")
            
            try:
                # Ensure directory exists one more time
                dir_name = os.path.dirname(abs_filename)
                os.makedirs(dir_name, exist_ok=True)
                
                print(f"DEBUG FileHandler: Directory created: {dir_name}")
                
                # Write with proper newline and flush
                with open(abs_filename, "a", encoding="utf-8") as f:
                    f.write(log_line + "\n")
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
                    
                print(f"DEBUG FileHandler: Successfully wrote to {abs_filename}")
            except Exception as e:
                print(f"DEBUG FileHandler: Failed to write to {abs_filename}: {e}")
                traceback.print_exc()
                raise

        except Exception as e:
            import traceback
            print(f"Failed to write log: {e}")
            traceback.print_exc()

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
            print(f"\nDEBUG FileHandler: Got record: level={record.level} message={record.message}")
            print(f"DEBUG FileHandler: My filename={self.filename} level={getattr(self, 'level', 'NOTSET')}")
            
            # Check level if specified
            if hasattr(self, 'level'):
                from ..types import LogLevel
                record_level = LogLevel.from_string(record.level)
                handler_level = LogLevel.from_string(self.level)
                print(f"DEBUG FileHandler: Record level={record_level} handler level={handler_level}")
                if record_level < handler_level:
                    print(f"DEBUG FileHandler: Skipping record due to level")
                    return
                    
            print(f"DEBUG FileHandler: Creating directory if needed")
            os.makedirs(os.path.dirname(os.path.abspath(self.filename)), exist_ok=True)
            
            print(f"DEBUG FileHandler: Emitting record")
            self.emit(record)
        except Exception as e:
            import traceback
            print(f"Failed to handle log: {e}")
            traceback.print_exc()

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