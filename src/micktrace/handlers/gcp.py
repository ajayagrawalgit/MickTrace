"""Google Cloud Platform (GCP) Logging handler for MickTrace.

This module provides handlers for Google Cloud Logging (formerly Stackdriver).
It serves as an alias to the StackdriverHandler for better discoverability.
"""

from .stackdriver import StackdriverHandler

# Alias for better naming - GCP is more recognizable than Stackdriver
GoogleCloudHandler = StackdriverHandler
GCPHandler = StackdriverHandler

__all__ = ["GoogleCloudHandler", "GCPHandler", "StackdriverHandler"]
