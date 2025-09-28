"""Base handlers for MickTrace."""

import logging
import os
import time
from typing import Any, Dict, List, Optional, TextIO, Union
from ..types import LogLevel, LogRecord


class Handler:
    """Base handler class for MickTrace."""
    
    def __init__(self, level: Optional[Union[str, LogLevel]] = None):
        self.level = LogLevel.from_string(level) if isinstance(level, str) else level or LogLevel.NOTSET
        self._filters: List[Any] = []

    def add_filter(self, filter_obj: Any) -> None:
        """Add a filter to the handler."""
        self._filters.append(filter_obj)

    def remove_filter(self, filter_obj: Any) -> None:
        """Remove a filter from the handler."""
        self._filters.remove(filter_obj)

    def handle(self, record: LogRecord) -> None:
        """Process a log record."""
        print(f"Handler {self.__class__.__name__} checking record: {record}")
        try:
            if not self.should_log(record):
                print(f"Handler {self.__class__.__name__} skipping record due to level/filters")
                return
            print(f"Handler {self.__class__.__name__} emitting record")
            self.emit(record)
        except Exception as e:
            print(f"Handler {self.__class__.__name__} failed to handle record: {e}")
            import traceback
            traceback.print_exc()

    def emit(self, record: LogRecord) -> None:
        """Emit a log record."""
        raise NotImplementedError

    def should_log(self, record: LogRecord) -> bool:
        """Check if record should be logged."""
        if not isinstance(record.level, LogLevel):
            record_level = LogLevel.from_string(record.level)
        else:
            record_level = record.level

        if not isinstance(self.level, LogLevel):
            handler_level = LogLevel.from_string(self.level)
        else:
            handler_level = self.level

        if record_level < handler_level:
            return False
            
        return all(f.filter(record) for f in self._filters)

    def flush(self) -> None:
        """Flush the handler."""
        pass

    def close(self) -> None:
        """Close the handler."""
        pass


class FileHandler(Handler):
    """Handler for writing log records to a file."""

    def __init__(
        self, 
        filename: str,
        mode: str = 'a',
        encoding: Optional[str] = None,
        level: Optional[Union[str, LogLevel]] = None,
        formatter: Optional[Any] = None
    ):
        super().__init__(level)
        self.filename = filename
        self.mode = mode
        self.encoding = encoding or 'utf-8'
        self.formatter = formatter
        self._file: Optional[TextIO] = None

    def _open(self) -> None:
        """Open the log file."""
        try:
            # Ensure directory exists
            directory = os.path.dirname(self.filename)
            if directory:
                os.makedirs(directory, exist_ok=True)
            self._file = open(self.filename, self.mode, encoding=self.encoding)
        except Exception as e:
            print(f"Failed to open log file {self.filename}: {e}")
            self._file = None

    def emit(self, record: LogRecord) -> None:
        """Write the record to the file."""
        try:
            # Ensure directory exists
            directory = os.path.dirname(self.filename)
            if directory:
                os.makedirs(directory, exist_ok=True)

            # Format the record using the formatter if available
            if self.formatter:
                msg = self.formatter.format(record)
            else:
                # Default formatting with better data handling
                ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.timestamp))
                msg = f"{ts} [{record.level:>8}] {record.logger_name} {record.message}"
                
                # Handle structured data
                if record.data:
                    try:
                        sorted_data = sorted(record.data.items())  # Sort for consistency
                        for k, v in sorted_data:
                            # Skip special fields
                            if k not in ('timestamp_iso', 'message'):
                                msg += f" {k}={v}"
                    except Exception:
                        pass  # Skip data on error

            # Write to file with proper newline
            msg += "\n"
            try:
                with open(self.filename, "a", encoding=self.encoding) as f:
                    f.write(msg)
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
            except OSError as ose:
                print(f"File write error: {ose} for file {self.filename}")
                raise
            except Exception as e:
                print(f"Unexpected error writing to {self.filename}: {e}")
                raise

            # Perform rollover check if needed
            if isinstance(self, RotatingFileHandler):
                self._do_rollover_if_needed()
        except Exception as e:
            # Use print for handler errors since we can't log them
            print(f"Failed to emit log record to {self.filename}: {e}")
            import traceback
            traceback.print_exc()

    def format(self, record: LogRecord) -> str:
        """Format the record."""
        if self.formatter:
            return self.formatter.format(record)
        return str(record)

    def flush(self) -> None:
        """Flush the file buffer."""
        if self._file is not None:
            self._file.flush()

    def close(self) -> None:
        """Close the file."""
        if self._file is not None:
            self._file.close()
            self._file = None


class RotatingFileHandler(FileHandler):
    """Handler for rotating log files when they reach a certain size."""

    def __init__(
        self,
        filename: str,
        max_bytes: int = 0,
        backup_count: int = 0,
        mode: str = 'a',
        encoding: Optional[str] = None,
        level: Optional[Union[str, LogLevel]] = None,
        formatter: Optional[Any] = None
    ):
        super().__init__(filename, mode, encoding, level, formatter)
        self.max_bytes = max_bytes
        self.backup_count = backup_count

    def should_rollover(self) -> bool:
        """Determine if rollover should occur."""
        if not self._file or self.max_bytes <= 0:
            return False
        try:
            self._file.seek(0, 2)  # Seek to end of file
            if self._file.tell() >= self.max_bytes:
                return True
        except Exception:
            pass
        return False

    def _do_rollover_if_needed(self) -> None:
        """Check if rollover is needed and perform it if necessary."""
        try:
            if not os.path.exists(self.filename):
                return

            if self.max_bytes > 0:
                if os.path.getsize(self.filename) >= self.max_bytes:
                    if self.backup_count > 0:
                        # Rotate existing backup files
                        for i in range(self.backup_count - 1, 0, -1):
                            sfn = f"{self.filename}.{i}"
                            dfn = f"{self.filename}.{i + 1}"
                            if os.path.exists(sfn):
                                if os.path.exists(dfn):
                                    os.remove(dfn)
                                os.rename(sfn, dfn)
                        dfn = f"{self.filename}.1"
                        if os.path.exists(dfn):
                            os.remove(dfn)
                        os.rename(self.filename, dfn)
                    else:
                        # If no backups are wanted, just truncate the file
                        with open(self.filename, "w") as f:
                            f.truncate(0)
        except Exception as e:
            print(f"Failed to rollover log file {self.filename}: {e}")