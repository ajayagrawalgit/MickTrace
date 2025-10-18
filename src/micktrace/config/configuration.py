"""
Configuration system for micktrace with comprehensive error handling.
Handles environment variables, validation, and hot-reload capabilities.
"""

import os
import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Import LogLevel from parent types module
from ..types import LogLevel


@dataclass
class HandlerConfig:
    """Configuration for a single handler with validation."""
    type: str
    level: str = "INFO"
    format: str = "structured"
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate handler configuration with error handling."""
        try:
            # Validate handler type
            valid_types = [
                "console", "file", "http", "syslog", "null", "memory", "stream"
            ]
            if not isinstance(self.type, str) or self.type not in valid_types:
                raise ValueError(
                    f"Invalid handler type: {self.type}. Must be one of {valid_types}")

            # Validate and normalize level
            try:
                LogLevel.from_string(self.level)
            except ValueError:
                # Default to INFO if invalid level
                self.level = "INFO"

            # Ensure format is valid
            valid_formats = ["json", "logfmt", "structured", "rich", "simple"]
            if not isinstance(self.format, str) or self.format not in valid_formats:
                self.format = "structured"

            # Ensure enabled is boolean
            if not isinstance(self.enabled, bool):
                self.enabled = bool(self.enabled)

            # Ensure config is dict
            if not isinstance(self.config, dict):
                self.config = {}

        except Exception:
            # If validation fails completely, set safe defaults
            self.type = "null"  # Use NullHandler as safe default
            self.level = "INFO"
            self.format = "structured"
            self.enabled = True
            self.config = {}


@dataclass
class Configuration:
    """Main micktrace configuration with comprehensive validation."""

    # Basic settings
    level: str = "INFO"
    format: str = "structured"
    enabled: bool = True
    is_configured: bool = False

    # Handlers
    handlers: List[HandlerConfig] = field(default_factory=lambda: [
        HandlerConfig(type="null")  # Use NullHandler by default
    ])

    # Context and metadata
    service: Optional[str] = None
    version: Optional[str] = None
    environment: str = "development"

    def __post_init__(self) -> None:
        """Post-initialization validation with error handling."""
        try:
            self.validate()
        except Exception:
            # If validation fails, ensure we have a working configuration
            self._set_safe_defaults()

    def _set_safe_defaults(self) -> None:
        """Set safe default values."""
        try:
            self.level = "INFO"
            self.format = "structured"
            self.enabled = True
            self.environment = "development"
            # Use NullHandler as safe default
            self.handlers = [HandlerConfig(type="null")]
        except Exception:
            pass

    def validate(self) -> None:
        """Validate configuration with error handling."""
        # Validate log level
        try:
            LogLevel.from_string(self.level)
        except ValueError:
            self.level = "INFO"

        # Validate format
        valid_formats = ["json", "logfmt", "structured", "rich", "simple"]
        if not isinstance(self.format, str) or self.format not in valid_formats:
            self.format = "structured"

        # Ensure enabled is boolean
        if not isinstance(self.enabled, bool):
            self.enabled = bool(self.enabled)

        # Validate environment
        if not isinstance(self.environment, str):
            self.environment = "development"

        # Validate handlers
        if not isinstance(self.handlers, list) or not self.handlers:
            # Use NullHandler as fallback
            self.handlers = [HandlerConfig(type="null")]
        else:
            # Validate each handler
            valid_handlers = []
            for handler in self.handlers:
                try:
                    if isinstance(handler, dict):
                        # Convert dict to HandlerConfig
                        handler_config = HandlerConfig(
                            type=handler.get("type", "console"),
                            level=handler.get("level", "INFO"),
                            format=handler.get("format", "structured"),
                            enabled=handler.get("enabled", True),
                            config={k: v for k, v in handler.items()
                                    if k not in ["type", "level", "format", "enabled"]}
                        )
                        valid_handlers.append(handler_config)
                    elif isinstance(handler, HandlerConfig):
                        valid_handlers.append(handler)
                    else:
                        # Skip invalid handlers
                        continue
                except Exception:
                    continue

            self.handlers = valid_handlers if valid_handlers else [
                HandlerConfig(type="console")]

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary with error handling."""
        try:
            handlers_list = []
            for handler in self.handlers:
                try:
                    handler_dict = {
                        "type": handler.type,
                        "level": handler.level,
                        "format": handler.format,
                        "enabled": handler.enabled,
                    }
                    handler_dict.update(handler.config)
                    handlers_list.append(handler_dict)
                except Exception:
                    # Skip invalid handlers
                    continue

            return {
                "level": self.level,
                "format": self.format,
                "enabled": self.enabled,
                "is_configured": self.is_configured,
                "service": self.service,
                "version": self.version,
                "environment": self.environment,
                "handlers": handlers_list
            }
        except Exception:
            # Fallback dict
            return {
                "level": "INFO",
                "format": "structured",
                "enabled": True,
                "is_configured": False,
                "handlers": [{"type": "null"}]  # Use NullHandler as fallback
            }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Configuration":
        """Create configuration from dictionary with error handling."""
        try:
            if not isinstance(data, dict):
                data = {}

            # Create handlers
            handlers = []
            handlers_data = data.get("handlers", [])

            if not isinstance(handlers_data, list):
                handlers_data = []

            for handler_data in handlers_data:
                try:
                    if isinstance(handler_data, dict):
                        handler_config = HandlerConfig(
                            type=handler_data.get("type", "console"),
                            level=handler_data.get("level", "INFO"),
                            format=handler_data.get("format", "structured"),
                            enabled=handler_data.get("enabled", True),
                            config={k: v for k, v in handler_data.items()
                                    if k not in ["type", "level", "format", "enabled"]}
                        )
                        handlers.append(handler_config)
                except Exception:
                    continue

            # Ensure at least one handler
            if not handlers:
                handlers = [HandlerConfig(type="console")]

            config = cls(
                level=data.get("level", "INFO"),
                format=data.get("format", "structured"),
                enabled=data.get("enabled", True),
                service=data.get("service"),
                version=data.get("version"),
                environment=data.get("environment", "development"),
                handlers=handlers,
                is_configured=data.get("is_configured", True)
            )

            return config

        except Exception:
            # Return default configuration if parsing fails
            return cls()

    @classmethod
    def from_env(cls) -> "Configuration":
        """Create configuration from environment variables with error handling."""
        try:
            # Parse handlers
            handler_types_str = os.getenv("MICKTRACE_HANDLERS", "console")
            handler_types = [h.strip()
                             for h in handler_types_str.split(",") if h.strip()]

            if not handler_types:
                handler_types = ["console"]

            handlers = []

            for handler_type in handler_types:
                try:
                    handler_config = HandlerConfig(
                        type=handler_type,
                        level=os.getenv(
                            f"MICKTRACE_{handler_type.upper()}_LEVEL", "INFO")
                    )

                    # Handler-specific config
                    if handler_type == "file":
                        file_path = os.getenv(
                            "MICKTRACE_FILE_PATH", "/tmp/micktrace.log")
                        handler_config.config["path"] = file_path

                        rotation = os.getenv("MICKTRACE_FILE_ROTATION")
                        if rotation:
                            handler_config.config["rotation"] = rotation

                    elif handler_type == "http":
                        url = os.getenv("MICKTRACE_HTTP_URL")
                        if url:
                            handler_config.config["url"] = url

                    handlers.append(handler_config)

                except Exception:
                    # Skip invalid handler configurations
                    continue

            # Ensure at least one handler
            if not handlers:
                handlers = [HandlerConfig(type="console")]

            config = cls(
                level=os.getenv("MICKTRACE_LEVEL", "INFO"),
                format=os.getenv("MICKTRACE_FORMAT", "structured"),
                enabled=os.getenv("MICKTRACE_ENABLED", "true").lower() in (
                    "true", "1", "yes"),
                service=os.getenv("MICKTRACE_SERVICE"),
                version=os.getenv("MICKTRACE_VERSION"),
                environment=os.getenv("MICKTRACE_ENVIRONMENT", "development"),
                handlers=handlers,
                is_configured=True
            )

            return config

        except Exception:
            # Return default configuration if environment parsing fails
            return cls()


# Global configuration management with thread safety
_config_lock = threading.RLock()
_global_config: Optional[Configuration] = None


def get_configuration() -> Configuration:
    """Get the global configuration instance with error handling."""
    global _global_config

    with _config_lock:
        if _global_config is None:
            try:
                # Try environment variables first
                _global_config = Configuration.from_env()
            except Exception:
                try:
                    # Fallback to default configuration
                    _global_config = Configuration()
                except Exception:
                    # Ultimate fallback - manually create minimal config
                    _global_config = Configuration.__new__(Configuration)
                    _global_config.level = "INFO"
                    _global_config.format = "structured"
                    _global_config.enabled = True
                    _global_config.is_configured = False
                    _global_config.handlers = [HandlerConfig(type="console")]
                    _global_config.service = None
                    _global_config.version = None
                    _global_config.environment = "development"

        return _global_config


def set_configuration(config: Configuration) -> None:
    """Set the global configuration with error handling."""
    global _global_config

    with _config_lock:
        try:
            if isinstance(config, Configuration):
                config.validate()
                config.is_configured = True
                _global_config = config
            else:
                # Invalid config, keep current one
                pass
        except Exception:
            # If setting fails, don't change current config
            pass


def configure(**kwargs: Any) -> None:
    """Configure micktrace programmatically with error handling."""
    try:
        current_config = get_configuration()

        # Create new configuration from current + overrides
        config_dict = current_config.to_dict()

        # Handle simple overrides
        for key in ["level", "format", "enabled", "service", "version", "environment"]:
            if key in kwargs:
                config_dict[key] = kwargs[key]

        # Handle handler configuration
        if "handlers" in kwargs:
            handlers = kwargs["handlers"]
            if isinstance(handlers, str):
                handler_types = [h.strip()
                                 for h in handlers.split(",") if h.strip()]
                config_dict["handlers"] = [{"type": h} for h in handler_types]
            elif isinstance(handlers, list):
                if all(isinstance(h, str) for h in handlers):
                    config_dict["handlers"] = [{"type": h} for h in handlers]
                elif all(isinstance(h, dict) for h in handlers):
                    config_dict["handlers"] = handlers
                else:
                    # Mixed or invalid types, keep current handlers
                    pass

        # Create and set new configuration
        new_config = Configuration.from_dict(config_dict)
        set_configuration(new_config)

    except Exception:
        # If configuration fails, silently continue with current config
        pass


def reset_configuration() -> None:
    """Reset configuration to defaults with error handling."""
    global _global_config

    with _config_lock:
        try:
            _global_config = Configuration()
        except Exception:
            # If reset fails, create minimal config
            _global_config = Configuration.__new__(Configuration)
            _global_config.level = "INFO"
            _global_config.format = "structured"
            _global_config.enabled = True
            _global_config.is_configured = False
            _global_config.handlers = [HandlerConfig(type="console")]
            _global_config.service = None
            _global_config.version = None
            _global_config.environment = "development"
