"""
Micktrace - The world's most advanced Python logging library

Zero-shortcomings, async-native, structured logging library designed to be 
the de facto standard for Python logging.

Key Features:
- Library-first design with zero global state pollution
- Async-native with sub-microsecond overhead when disabled  
- Structured logging by default with type safety
- Hot-reload configuration and environment variable support
- Multiprocessing safe with built-in queue management
- Cloud-native with OpenTelemetry integration
- Built-in redaction, rotation, compression, and dead letter queues

Example:
    >>> import micktrace
    >>> logger = micktrace.get_logger(__name__)
    >>> logger.info("Hello world", user_id=123, action="login")

    >>> # Configure for applications
    >>> micktrace.configure(level="INFO", format="json")
"""

from typing import Any, Dict, List, Optional, Union

from .core.logger import Logger, get_logger
from .config.configuration import configure, get_configuration
from .core.context import context, get_context, set_context
from .core.tracing import trace, timer, now, elapsed
from .handlers.base import Handler
from .formatters.base import Formatter
from .filters.base import Filter
from . import testing

# Version information
__version__ = "1.0.0"
__author__ = "Ajay Agrawal"
__email__ = "ajay@micktrace.dev"
__license__ = "MIT"

# Public API
__all__ = [
    # Core functionality
    "get_logger",
    "configure", 
    "get_configuration",

    # Context management
    "context",
    "get_context", 
    "set_context",

    # Tracing and timing
    "trace",
    "timer",
    "now",
    "elapsed", 

    # Base classes for extensions
    "Logger",
    "Handler",
    "Formatter", 
    "Filter",

    # Testing utilities
    "testing",

    # Version info
    "__version__",
    "__author__", 
    "__email__",
    "__license__"
]

# Convenience functions for quick setup
def basic_config(**kwargs: Any) -> None:
    """Quick configuration for simple use cases.

    Args:
        **kwargs: Configuration options passed to configure()

    Example:
        >>> micktrace.basic_config(level="INFO", format="json")
    """
    configure(**kwargs)

def disable() -> None:
    """Disable all logging output.

    Useful for tests or when you want to completely silence logging.
    """
    configure(level="CRITICAL", handlers=[])

def enable() -> None: 
    """Re-enable logging after disable().

    Restores default configuration.
    """
    configure(level="INFO", handlers=["console"])
