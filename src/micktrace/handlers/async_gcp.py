"""Async Google Cloud Platform (GCP) Logging handler for MickTrace.

This module provides async handlers for Google Cloud Logging (formerly Stackdriver).
It serves as an alias to the AsyncGoogleCloudHandler for better discoverability.
"""

from .async_stackdriver import AsyncGoogleCloudHandler

# Alias for better naming
AsyncGCPHandler = AsyncGoogleCloudHandler

__all__ = ["AsyncGCPHandler", "AsyncGoogleCloudHandler"]
