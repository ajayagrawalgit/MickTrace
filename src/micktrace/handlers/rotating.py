"""Rotating file handler implementation."""

import os
from pathlib import Path
from typing import Optional

from .handlers import FileHandler
from ..types import LogRecord


class RotatingFileHandler(FileHandler):
    """A handler that writes log records to a file, rotating the file when it reaches a certain size."""

    def __init__(self, name: str, level: str = "INFO", formatter: Optional[object] = None,
                 filename: str = "log.txt", maxBytes: int = 0, backupCount: int = 0,
                 encoding: str = "utf-8", errors: str = "strict", **kwargs):
        """Initialize the handler."""
        super().__init__(name=name, level=level, formatter=formatter, 
                        filename=filename, encoding=encoding, errors=errors)
        
        self.maxBytes = maxBytes
        self.backupCount = backupCount
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        """Ensure the log directory exists."""
        try:
            log_dir = Path(self.filename).parent
            log_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def _should_rotate(self) -> bool:
        """Determine if we should rotate the file."""
        if self.maxBytes <= 0:
            return False
            
        try:
            if not os.path.exists(self.filename):
                return False
            return os.path.getsize(self.filename) >= self.maxBytes
        except Exception:
            return False

    def _do_rotation(self) -> None:
        """Perform log rotation."""
        if not os.path.exists(self.filename):
            return

        try:
            if self.backupCount > 0:
                # Delete the oldest backup if it exists
                oldest = f"{self.filename}.{self.backupCount}"
                if os.path.exists(oldest):
                    os.remove(oldest)

                # Rotate existing backups
                for i in range(self.backupCount - 1, 0, -1):
                    source = f"{self.filename}.{i}"
                    dest = f"{self.filename}.{i + 1}"
                    if os.path.exists(source):
                        os.rename(source, dest)

                # Rotate current file
                if os.path.exists(self.filename):
                    os.rename(self.filename, f"{self.filename}.1")

            else:
                # No backups, just truncate
                open(self.filename, 'w').close()

        except Exception:
            pass

    def handle(self, record: LogRecord) -> None:
        """Handle a log record with rotation support."""
        try:
            if self._should_rotate():
                self._do_rotation()
                if hasattr(self, '_file') and self._file:
                    self._file.close()
                    self._file = None

            super().handle(record)
        except Exception:
            pass

    def close(self) -> None:
        """Close the handler and associated file."""
        try:
            super().close()
        except Exception:
            pass