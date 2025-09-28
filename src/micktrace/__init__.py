"""
Micktrace - The world's most advanced Python logging library

Created by Ajay Agrawal (https://github.com/ajayagrawalgit)
Repository: https://github.com/ajayagrawalgit/MickTrace
LinkedIn: https://www.linkedin.com/in/theajayagrawal/
Copyright (c) 2025 Ajay Agrawal. All rights reserved.

Zero-shortcomings, async-native, structured logging library designed to be 
the de facto standard for Python logging.

Features:
- Library-first design with zero global state pollution
- Async-native with sub-microsecond overhead when disabled  
- Structured logging by default with type safety
- Hot-reload configuration and environment variable support
- Multiprocessing safe with built-in queue management
- Comprehensive error handling throughout

Example:
    >>> import micktrace
    >>> logger = micktrace.get_logger(__name__)
    >>> logger.info("Hello world", user_id=123, action="login")

    >>> # Configure for applications
    >>> micktrace.configure(level="INFO", format="json")
"""

from typing import Any, Dict, Optional

# Core functionality - import carefully to avoid circular imports
from .core.logger import Logger, BoundLogger, get_logger, bind
from .config.configuration import configure, get_configuration
from .core.context import (
    Context, 
    ContextProvider, 
    DynamicContext,
    get_context,
    set_context,
    clear_context,
    context,
    acontext,
    correlation,
    acorrelation
)

# Types
from .types import LogLevel, LogRecord

# Import base classes for extensions
try:
    from .handlers import ConsoleHandler, NullHandler, MemoryHandler
except ImportError:
    # Graceful fallback if handlers not available
    ConsoleHandler = None
    NullHandler = None
    MemoryHandler = None

try:
    from .formatters import Formatter, JSONFormatter, SimpleFormatter
except ImportError:
    # Graceful fallback if formatters not available
    Formatter = None
    JSONFormatter = None
    SimpleFormatter = None

try:
    from .filters import Filter, LevelFilter
except ImportError:
    # Graceful fallback if filters not available
    Filter = None
    LevelFilter = None

# Version and metadata
__version__ = "1.0.0"
__author__ = "Ajay Agrawal"
__email__ = "ajayagrawalofficial@gmail.com"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2025 Ajay Agrawal"
__url__ = "https://github.com/ajayagrawalgit/MickTrace"
__repository__ = "https://github.com/ajayagrawalgit/MickTrace"
__linkedin__ = "https://www.linkedin.com/in/theajayagrawal/"
__credits__ = ["Ajay Agrawal"]

# Public API
__all__ = [
    # Core functionality
    "get_logger",
    "configure", 
    "get_configuration",
    "bind",

    # Context management
    "context",
    "acontext",
    "get_context", 
    "set_context",
    "clear_context",

    # Types
    "Logger",
    "BoundLogger",
    "LogLevel",
    "LogRecord",

    # Base classes for extensions (may be None if imports fail)
    "ConsoleHandler",
    "NullHandler", 
    "MemoryHandler",
    "Formatter",
    "JSONFormatter",
    "SimpleFormatter",
    "Filter",
    "LevelFilter",

    # Version info
    "__version__",
    "__author__", 
    "__email__",
    "__license__"
]


def basic_config(**kwargs: Any) -> None:
    """Quick configuration for simple use cases.

    Args:
        **kwargs: Configuration options passed to configure()

    Example:
        >>> import micktrace
        >>> micktrace.basic_config(level="INFO", format="json")
    """
    try:
        configure(**kwargs)
    except Exception:
        # If configuration fails, continue silently
        pass


def disable() -> None:
    """Disable all logging output.

    Useful for tests or when you want to completely silence logging.
    """
    try:
        configure(enabled=False)
    except Exception:
        pass


def enable() -> None: 
    """Re-enable logging after disable().

    Restores default configuration.
    """
    try:
        configure(enabled=True, level="INFO")
    except Exception:
        pass


# Library compatibility functions
def getLogger(name: Optional[str] = None) -> Logger:
    """Get logger - compatibility with stdlib logging."""
    return get_logger(name)


def setLevel(level: str) -> None:
    """Set global log level - compatibility function."""
    try:
        configure(level=level)
    except Exception:
        pass
