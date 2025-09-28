"""Rich text console formatters with color support."""

import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from ..types import LogRecord


class ColorizedFormatter:
    """A formatter that adds ANSI colors to log output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    LEVEL_COLORS = {
        "DEBUG": BLUE,
        "INFO": GREEN,
        "WARNING": YELLOW,
        "ERROR": RED,
        "CRITICAL": RED + BOLD,
    }

    def __init__(self, timestamp_format: str = "%Y-%m-%d %H:%M:%S",
                 include_context: bool = True, colored_level: bool = True,
                 colored_service: bool = False) -> None:
        """Initialize the formatter."""
        self.timestamp_format = timestamp_format
        self.include_context = include_context
        self.colored_level = colored_level
        self.colored_service = colored_service
        self._check_color_support()

    def _check_color_support(self) -> None:
        """Check if the terminal supports colors."""
        self.supports_color = False
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            self.supports_color = True

    def _colorize(self, text: str, color: str) -> str:
        """Add color to text if supported."""
        if self.supports_color:
            return f"{color}{text}{self.RESET}"
        return text

    def _format_level(self, level: str) -> str:
        """Format the log level with color."""
        if self.colored_level:
            color = self.LEVEL_COLORS.get(level, self.WHITE)
            return self._colorize(f"[{level:>8}]", color)
        return f"[{level:>8}]"

    def _format_timestamp(self, timestamp: float) -> str:
        """Format the timestamp."""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime(self.timestamp_format)
        except Exception:
            return str(timestamp)

    def _format_service(self, logger_name: str) -> str:
        """Format the service/logger name."""
        if self.colored_service:
            return self._colorize(logger_name, self.CYAN)
        return logger_name

    def _format_data(self, data: Dict[str, Any]) -> str:
        """Format additional data fields."""
        try:
            parts = []
            for key, value in data.items():
                if key not in ['timestamp_iso', 'level', 'logger_name', 'message']:
                    try:
                        if isinstance(value, (dict, list)):
                            value_str = json.dumps(value)
                        else:
                            value_str = str(value)
                        parts.append(f"{key}={value_str}")
                    except Exception:
                        parts.append(f"{key}=<error>")
            return " ".join(parts)
        except Exception:
            return ""

    def format(self, record: LogRecord) -> str:
        """Format a log record with color support."""
        try:
            # Build the basic log message
            parts = [
                self._format_timestamp(record.timestamp),
                self._format_level(record.level),
                self._format_service(record.logger_name),
                record.message
            ]

            # Add context data if enabled
            if self.include_context and record.data:
                data_str = self._format_data(record.data)
                if data_str:
                    parts.append(data_str)

            # Add exception information if present
            if record.exception:
                try:
                    exc_info = (
                        f"\nException: {record.exception.get('type', 'Unknown')}: "
                        f"{record.exception.get('message', 'No message')}"
                    )
                    parts.append(self._colorize(exc_info, self.RED))
                except Exception:
                    pass

            return " ".join(str(p) for p in parts if p)

        except Exception as e:
            # Fallback formatting
            return f"Failed to format log record: {e}"