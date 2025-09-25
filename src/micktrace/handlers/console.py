"""
Console Handler

High-performance console output with rich formatting, colors,
and intelligent fallbacks.
"""

import sys
import threading
from typing import Any, Dict, List, TextIO, Optional

from .base import Handler
from ..core.record import LogRecord

# Try to import rich for enhanced console output
try:
    from rich.console import Console
    from rich.highlighter import ReprHighlighter
    from rich.text import Text
    from rich.theme import Theme
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# ANSI color codes for fallback
COLORS = {
    'DEBUG': '[36m',      # Cyan
    'INFO': '[32m',       # Green  
    'WARNING': '[33m',    # Yellow
    'ERROR': '[31m',      # Red
    'CRITICAL': '[35m',   # Magenta
    'RESET': '[0m'        # Reset
}


class ConsoleHandler(Handler):
    """
    Console handler with rich formatting and color support.

    Features:
    - Rich console output when available
    - ANSI color fallback
    - Intelligent stream selection (stdout/stderr)
    - Thread-safe output
    - Structured data pretty-printing
    """

    def __init__(
        self,
        name: str = "console",
        stream: Optional[TextIO] = None,
        use_colors: bool = True,
        rich_format: bool = True,
        **kwargs: Any
    ) -> None:
        super().__init__(name, **kwargs)

        # Stream configuration
        if stream is None:
            # Use stderr for warnings and above, stdout for others
            self.use_smart_streams = True
            self.stdout_stream = sys.stdout
            self.stderr_stream = sys.stderr
        else:
            self.use_smart_streams = False
            self.stream = stream

        self.use_colors = use_colors and self._supports_color()
        self.rich_format = rich_format and HAS_RICH

        # Thread safety
        self._write_lock = threading.Lock()

        # Rich console setup
        if self.rich_format:
            self.rich_console = Console(
                file=sys.stderr if self.use_smart_streams else stream,
                force_terminal=self.use_colors,
                theme=Theme({
                    "debug": "cyan",
                    "info": "green", 
                    "warning": "yellow",
                    "error": "red",
                    "critical": "bold red"
                })
            )
            self.highlighter = ReprHighlighter()

    def _supports_color(self) -> bool:
        """Check if the terminal supports colors."""
        # Check if we're in a TTY
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return False

        # Check environment variables
        import os
        if os.environ.get('NO_COLOR'):
            return False

        if os.environ.get('FORCE_COLOR'):
            return True

        # Check TERM environment variable
        term = os.environ.get('TERM', '').lower()
        if 'color' in term or term in ('xterm', 'xterm-256color', 'screen'):
            return True

        return False

    def _get_stream(self, record: LogRecord) -> TextIO:
        """Get the appropriate output stream for the record."""
        if not self.use_smart_streams:
            return self.stream

        # Use stderr for warnings and above
        if record.level in ('WARNING', 'ERROR', 'CRITICAL'):
            return self.stderr_stream
        else:
            return self.stdout_stream

    def _format_rich(self, record: LogRecord) -> None:
        """Format record using Rich."""
        if not self.rich_format:
            return

        # Create timestamp
        from datetime import datetime
        timestamp = datetime.fromtimestamp(record.timestamp)
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Create level with color
        level_style = record.level.lower()
        level_text = Text(f"[{record.level:>8}]", style=level_style)

        # Create logger name
        logger_text = Text(f"{record.logger_name}", style="dim")

        # Create message
        message_text = Text(record.message)
        if record.data:
            # Add structured data
            data_parts = []
            for key, value in record.data.items():
                if key != 'timestamp_iso':  # Skip internal timestamp
                    data_parts.append(f"{key}={value}")

            if data_parts:
                data_text = " " + " ".join(data_parts)
                message_text.append(Text(data_text, style="dim"))

        # Combine all parts
        console_text = Text()
        console_text.append(f"{timestamp_str} ")
        console_text.append(level_text)
        console_text.append(" ")
        console_text.append(logger_text)
        console_text.append(" ")
        console_text.append(message_text)

        # Add exception info if present
        if record.exception:
            console_text.append("
")
            exc_text = Text(f"Exception: {record.exception['type']}: {record.exception['message']}", 
                           style="red")
            console_text.append(exc_text)

        # Print to console
        stream = self._get_stream(record)
        console = Console(file=stream, force_terminal=self.use_colors)
        console.print(console_text)

    def _format_plain(self, record: LogRecord) -> str:
        """Format record as plain text with optional colors."""
        from datetime import datetime
        timestamp = datetime.fromtimestamp(record.timestamp)
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Build formatted message
        parts = [
            timestamp_str,
            f"[{record.level:>8}]",
            record.logger_name,
            record.message
        ]

        # Add structured data
        if record.data:
            data_parts = []
            for key, value in record.data.items():
                if key != 'timestamp_iso':
                    data_parts.append(f"{key}={value}")

            if data_parts:
                parts.append(" ".join(data_parts))

        message = " ".join(parts)

        # Add colors if enabled
        if self.use_colors:
            color = COLORS.get(record.level, '')
            reset = COLORS['RESET']

            # Color the level part
            message = message.replace(
                f"[{record.level:>8}]",
                f"{color}[{record.level:>8}]{reset}"
            )

        # Add exception info
        if record.exception:
            exc_info = f"
Exception: {record.exception['type']}: {record.exception['message']}"
            if self.use_colors:
                exc_info = f"{COLORS['ERROR']}{exc_info}{COLORS['RESET']}"
            message += exc_info

        return message

    def _emit_sync(self, formatted: str, record: LogRecord) -> None:
        """Emit a single record synchronously."""
        with self._write_lock:
            if self.rich_format:
                self._format_rich(record)
            else:
                stream = self._get_stream(record)
                stream.write(formatted + '
')
                stream.flush()

    async def _emit_async(self, formatted_records: List[str], records: List[LogRecord]) -> None:
        """Emit a batch of records asynchronously."""
        with self._write_lock:
            if self.rich_format:
                for record in records:
                    self._format_rich(record)
            else:
                # Group by stream for efficiency
                stdout_messages = []
                stderr_messages = []

                for formatted, record in zip(formatted_records, records):
                    if self.use_smart_streams:
                        if record.level in ('WARNING', 'ERROR', 'CRITICAL'):
                            stderr_messages.append(formatted)
                        else:
                            stdout_messages.append(formatted)
                    else:
                        stdout_messages.append(formatted)

                # Write batches
                if stdout_messages:
                    self.stdout_stream.write('
'.join(stdout_messages) + '
')
                    self.stdout_stream.flush()

                if stderr_messages:
                    self.stderr_stream.write('
'.join(stderr_messages) + '
') 
                    self.stderr_stream.flush()

    def format_record(self, record: LogRecord) -> str:
        """Format a log record."""
        if self.rich_format:
            # Rich formatting is handled in _emit methods
            return ""
        else:
            return self._format_plain(record)
