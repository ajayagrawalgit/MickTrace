"""Logging handlers for micktrace."""

from .console import ConsoleHandler, NullHandler, MemoryHandler
from .file import FileHandler
from .rotating import RotatingFileHandler
from .cloudwatch import CloudWatchHandler
from .stackdriver import StackdriverHandler
from .gcp import GoogleCloudHandler, GCPHandler
from .azure import AzureMonitorHandler
from .async_base import AsyncHandler, AsyncBatchHandler
from .buffered import BufferedHandler
from .datadog import DatadogHandler

# Optional async handlers - import only if dependencies are available
try:
    from .async_cloudwatch import AsyncCloudWatchHandler
except ImportError:
    AsyncCloudWatchHandler = None

try:
    from .async_stackdriver import AsyncGoogleCloudHandler
    from .async_gcp import AsyncGCPHandler
except ImportError:
    AsyncGoogleCloudHandler = None
    AsyncGCPHandler = None

try:
    from .async_azure import AsyncAzureMonitorHandler
except ImportError:
    AsyncAzureMonitorHandler = None

__all__ = [
    "ConsoleHandler",
    "NullHandler",
    "MemoryHandler",
    "FileHandler",
    "CloudWatchHandler",
    "StackdriverHandler",
    "GoogleCloudHandler",
    "GCPHandler",
    "AzureMonitorHandler",
    "DatadogHandler",
    "AsyncHandler",
    "AsyncBatchHandler",
    "BufferedHandler",
    "RotatingFileHandler",
]

# Add async handlers to __all__ if they were successfully imported
if AsyncCloudWatchHandler is not None:
    __all__.append("AsyncCloudWatchHandler")
if AsyncGoogleCloudHandler is not None:
    __all__.append("AsyncGoogleCloudHandler")
if AsyncGCPHandler is not None:
    __all__.append("AsyncGCPHandler")
if AsyncAzureMonitorHandler is not None:
    __all__.append("AsyncAzureMonitorHandler")
