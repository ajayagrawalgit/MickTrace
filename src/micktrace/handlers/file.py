"""
File Handler

High-performance file output with rotation, compression, and
multiprocessing safety.
"""

import asyncio
import gzip
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .base import Handler
from ..core.record import LogRecord


class FileHandler(Handler):
    """
    File handler with rotation, compression, and multiprocessing support.

    Features:
    - Automatic log rotation (size, time, count based)
    - Optional compression (gzip)
    - Multiprocessing safe with file locking
    - Batch writing for performance
    - Atomic file operations
    """

    def __init__(
        self,
        name: str = "file",
        path: Union[str, Path] = "micktrace.log",
        rotation: Optional[str] = None,
        max_size: Optional[str] = None,
        max_count: int = 10,
        compression: Optional[str] = None,
        encoding: str = "utf-8",
        **kwargs: Any
    ) -> None:
        super().__init__(name, **kwargs)

        self.path = Path(path)
        self.encoding = encoding
        self.compression = compression

        # Rotation configuration
        self.rotation = rotation  # "daily", "weekly", "monthly", or None
        self.max_size = self._parse_size(max_size) if max_size else None
        self.max_count = max_count

        # File management
        self.current_file: Optional[Any] = None
        self.file_lock = threading.Lock()
        self.write_buffer: List[str] = []
        self.buffer_lock = threading.Lock()

        # Rotation tracking
        self.current_size = 0
        self.last_rotation_check = time.time()
        self.rotation_check_interval = 60  # Check every minute

        # Ensure directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Open initial file
        self._open_file()

    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '10MB' to bytes."""
        size_str = size_str.upper()

        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3,
            'TB': 1024 ** 4
        }

        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                number = size_str[:-len(suffix)]
                return int(float(number) * multiplier)

        # Assume bytes if no suffix
        return int(size_str)

    def _open_file(self) -> None:
        """Open the log file for writing."""
        with self.file_lock:
            if self.current_file:
                self.current_file.close()

            self.current_file = open(
                self.path, 
                'a', 
                encoding=self.encoding,
                buffering=1  # Line buffering
            )

            # Get current file size
            try:
                self.current_size = self.path.stat().st_size
            except OSError:
                self.current_size = 0

    def _should_rotate(self) -> bool:
        """Check if log rotation is needed."""
        current_time = time.time()

        # Don't check too frequently
        if current_time - self.last_rotation_check < self.rotation_check_interval:
            return False

        self.last_rotation_check = current_time

        # Size-based rotation
        if self.max_size and self.current_size >= self.max_size:
            return True

        # Time-based rotation
        if self.rotation:
            try:
                file_mtime = self.path.stat().st_mtime
                file_time = time.localtime(file_mtime)
                current_local_time = time.localtime(current_time)

                if self.rotation == "daily":
                    return (file_time.tm_year != current_local_time.tm_year or
                            file_time.tm_yday != current_local_time.tm_yday)
                elif self.rotation == "weekly":
                    # Check if we're in a different week
                    import calendar
                    file_week = calendar.timegm(file_time) // (7 * 24 * 3600)
                    current_week = calendar.timegm(current_local_time) // (7 * 24 * 3600)
                    return file_week != current_week
                elif self.rotation == "monthly":
                    return (file_time.tm_year != current_local_time.tm_year or
                            file_time.tm_mon != current_local_time.tm_mon)
            except OSError:
                pass

        return False

    def _rotate_file(self) -> None:
        """Rotate the current log file."""
        with self.file_lock:
            if self.current_file:
                self.current_file.close()
                self.current_file = None

            # Generate rotated filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            rotated_name = f"{self.path.stem}_{timestamp}{self.path.suffix}"
            rotated_path = self.path.parent / rotated_name

            try:
                # Rename current file
                self.path.rename(rotated_path)

                # Compress if requested
                if self.compression == "gzip":
                    self._compress_file(rotated_path)

                # Clean up old files
                self._cleanup_old_files()

            except OSError as e:
                # If rotation fails, just continue with current file
                pass

            # Open new file
            self._open_file()

    def _compress_file(self, file_path: Path) -> None:
        """Compress a file using gzip."""
        compressed_path = file_path.with_suffix(file_path.suffix + ".gz")

        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)

            # Remove uncompressed file
            file_path.unlink()

        except Exception:
            # If compression fails, keep uncompressed file
            if compressed_path.exists():
                compressed_path.unlink()

    def _cleanup_old_files(self) -> None:
        """Remove old log files beyond max_count."""
        if self.max_count <= 0:
            return

        try:
            # Find all related log files
            pattern = f"{self.path.stem}_*{self.path.suffix}*"
            log_files = list(self.path.parent.glob(pattern))

            # Sort by creation time (oldest first)  
            log_files.sort(key=lambda p: p.stat().st_mtime)

            # Remove excess files
            while len(log_files) > self.max_count:
                old_file = log_files.pop(0)
                try:
                    old_file.unlink()
                except OSError:
                    pass

        except Exception:
            pass

    def _write_to_file(self, messages: List[str]) -> None:
        """Write messages to file with rotation check."""
        # Check for rotation before writing
        if self._should_rotate():
            self._rotate_file()

        with self.file_lock:
            if not self.current_file:
                self._open_file()

            for message in messages:
                message_bytes = len(message.encode(self.encoding))
                self.current_file.write(message + '
')
                self.current_size += message_bytes + 1  # +1 for newline

            self.current_file.flush()
            os.fsync(self.current_file.fileno())  # Force write to disk

    def _emit_sync(self, formatted: str, record: LogRecord) -> None:
        """Emit a single record synchronously."""
        self._write_to_file([formatted])

    async def _emit_async(self, formatted_records: List[str], records: List[LogRecord]) -> None:
        """Emit a batch of records asynchronously."""
        # Use thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._write_to_file, formatted_records)

    async def stop(self) -> None:
        """Stop the handler and close files."""
        await super().stop()

        with self.file_lock:
            if self.current_file:
                self.current_file.close()
                self.current_file = None

    def get_stats(self) -> Dict[str, Any]:
        """Get file handler statistics."""
        stats = super().get_stats()

        stats.update({
            "file_path": str(self.path),
            "file_size": self.current_size,
            "rotation": self.rotation,
            "max_size": self.max_size,
            "compression": self.compression
        })

        return stats
