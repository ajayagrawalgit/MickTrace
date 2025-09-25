"""
Configuration System

Provides flexible configuration for micktrace with support for:
- Environment variables
- Programmatic configuration  
- Hot-reload capabilities
- Validation and type safety
- Zero-config defaults for libraries
"""

import os
import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

# Global configuration instance
_config_lock = threading.RLock()
_global_config: Optional["Configuration"] = None


class LogFormat(Enum):
    """Supported log formats."""
    JSON = "json"
    LOGFMT = "logfmt" 
    STRUCTURED = "structured"
    RICH = "rich"
    SIMPLE = "simple"


@dataclass
class HandlerConfig:
    """Configuration for a single handler."""
    type: str
    level: str = "INFO"
    format: str = "structured"
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate handler configuration."""
        if self.type not in ["console", "file", "http", "syslog", "null", "memory"]:
            raise ValueError(f"Unknown handler type: {self.type}")


@dataclass  
class ContextConfig:
    """Configuration for automatic context injection."""
    service: Optional[str] = None
    version: Optional[str] = None
    environment: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SamplingConfig:
    """Configuration for log sampling."""
    rate: float = 1.0  # Sample rate (0.0 to 1.0)
    key: Optional[str] = None  # Key to use for consistent sampling
    enabled: bool = False


@dataclass
class PerformanceConfig:
    """Performance-related configuration."""
    async_enabled: bool = True
    queue_size: int = 10000
    batch_size: int = 100
    flush_interval: float = 1.0
    worker_count: int = 1


@dataclass
class RedactionConfig:
    """Configuration for automatic data redaction."""
    enabled: bool = True
    fields: List[str] = field(default_factory=lambda: [
        "password", "secret", "token", "key", "auth", "credential",
        "ssn", "social_security", "credit_card", "cc_number",
        "api_key", "private_key", "access_token", "refresh_token"
    ])
    replacement: str = "[REDACTED]"
    patterns: List[str] = field(default_factory=list)


@dataclass
class Configuration:
    """Main micktrace configuration."""

    # Basic settings
    level: str = "INFO"
    format: str = "structured"
    enabled: bool = True
    is_configured: bool = False

    # Handlers
    handlers: List[HandlerConfig] = field(default_factory=lambda: [
        HandlerConfig(type="console")
    ])

    # Context and metadata
    context: ContextConfig = field(default_factory=ContextConfig)

    # Performance 
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)

    # Sampling
    sampling: SamplingConfig = field(default_factory=SamplingConfig)

    # Security
    redaction: RedactionConfig = field(default_factory=RedactionConfig)

    # Advanced options
    correlation_id_header: str = "X-Correlation-ID"
    trace_id_header: str = "X-Trace-ID"
    timezone: str = "UTC"

    # Hot reload
    hot_reload: bool = False
    config_file: Optional[Path] = None

    def __post_init__(self) -> None:
        """Post-initialization validation."""
        self.validate()

    def validate(self) -> None:
        """Validate configuration."""
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "NOTSET"]
        if self.level.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {self.level}")

        # Validate format
        if self.format not in [f.value for f in LogFormat]:
            raise ValueError(f"Invalid format: {self.format}")

        # Validate sampling rate
        if not 0.0 <= self.sampling.rate <= 1.0:
            raise ValueError("Sampling rate must be between 0.0 and 1.0")

        # Validate handler configurations
        for handler in self.handlers:
            if handler.level.upper() not in valid_levels:
                raise ValueError(f"Invalid handler level: {handler.level}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {}

        result["level"] = self.level
        result["format"] = self.format
        result["enabled"] = self.enabled

        result["handlers"] = []
        for handler in self.handlers:
            result["handlers"].append({
                "type": handler.type,
                "level": handler.level,
                "format": handler.format,
                "enabled": handler.enabled,
                **handler.config
            })

        result["context"] = {
            "service": self.context.service,
            "version": self.context.version,
            "environment": self.context.environment,
            **self.context.extra
        }

        result["performance"] = {
            "async_enabled": self.performance.async_enabled,
            "queue_size": self.performance.queue_size,
            "batch_size": self.performance.batch_size,
            "flush_interval": self.performance.flush_interval,
            "worker_count": self.performance.worker_count
        }

        result["sampling"] = {
            "rate": self.sampling.rate,
            "key": self.sampling.key,
            "enabled": self.sampling.enabled
        }

        result["redaction"] = {
            "enabled": self.redaction.enabled,
            "fields": self.redaction.fields,
            "replacement": self.redaction.replacement,
            "patterns": self.redaction.patterns
        }

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Configuration":
        """Create configuration from dictionary."""
        config = cls()

        # Basic settings
        config.level = data.get("level", config.level)
        config.format = data.get("format", config.format) 
        config.enabled = data.get("enabled", config.enabled)

        # Handlers
        if "handlers" in data:
            config.handlers = []
            for handler_data in data["handlers"]:
                handler_config = HandlerConfig(
                    type=handler_data["type"],
                    level=handler_data.get("level", "INFO"),
                    format=handler_data.get("format", "structured"),
                    enabled=handler_data.get("enabled", True),
                    config={k: v for k, v in handler_data.items() 
                           if k not in ["type", "level", "format", "enabled"]}
                )
                config.handlers.append(handler_config)

        # Context
        if "context" in data:
            context_data = data["context"]
            config.context = ContextConfig(
                service=context_data.get("service"),
                version=context_data.get("version"), 
                environment=context_data.get("environment"),
                extra={k: v for k, v in context_data.items() 
                      if k not in ["service", "version", "environment"]}
            )

        # Performance
        if "performance" in data:
            perf_data = data["performance"]
            config.performance = PerformanceConfig(
                async_enabled=perf_data.get("async_enabled", True),
                queue_size=perf_data.get("queue_size", 10000),
                batch_size=perf_data.get("batch_size", 100),
                flush_interval=perf_data.get("flush_interval", 1.0),
                worker_count=perf_data.get("worker_count", 1)
            )

        # Sampling
        if "sampling" in data:
            sampling_data = data["sampling"]
            config.sampling = SamplingConfig(
                rate=sampling_data.get("rate", 1.0),
                key=sampling_data.get("key"),
                enabled=sampling_data.get("enabled", False)
            )

        # Redaction
        if "redaction" in data:
            redaction_data = data["redaction"]
            config.redaction = RedactionConfig(
                enabled=redaction_data.get("enabled", True),
                fields=redaction_data.get("fields", config.redaction.fields),
                replacement=redaction_data.get("replacement", "[REDACTED]"),
                patterns=redaction_data.get("patterns", [])
            )

        config.is_configured = True
        return config

    @classmethod
    def from_env(cls) -> "Configuration":
        """Create configuration from environment variables."""
        config = cls()

        # Basic settings from environment
        config.level = os.getenv("MICKTRACE_LEVEL", config.level)
        config.format = os.getenv("MICKTRACE_FORMAT", config.format)
        config.enabled = os.getenv("MICKTRACE_ENABLED", "true").lower() == "true"

        # Handler configuration from environment
        handler_types = os.getenv("MICKTRACE_HANDLERS", "console").split(",")
        config.handlers = []

        for handler_type in handler_types:
            handler_type = handler_type.strip()
            handler_config = HandlerConfig(type=handler_type)

            # Handler-specific config from environment
            if handler_type == "file":
                file_path = os.getenv("MICKTRACE_FILE_PATH", "/tmp/micktrace.log")
                handler_config.config["path"] = file_path

                rotation = os.getenv("MICKTRACE_FILE_ROTATION")
                if rotation:
                    handler_config.config["rotation"] = rotation

            elif handler_type == "http":
                url = os.getenv("MICKTRACE_HTTP_URL")
                if url:
                    handler_config.config["url"] = url

            config.handlers.append(handler_config)

        # Context from environment
        config.context = ContextConfig(
            service=os.getenv("MICKTRACE_SERVICE"),
            version=os.getenv("MICKTRACE_VERSION"),
            environment=os.getenv("MICKTRACE_ENVIRONMENT", "development")
        )

        # Performance settings
        if os.getenv("MICKTRACE_ASYNC_ENABLED"):
            config.performance.async_enabled = (
                os.getenv("MICKTRACE_ASYNC_ENABLED", "true").lower() == "true"
            )

        if os.getenv("MICKTRACE_QUEUE_SIZE"):
            config.performance.queue_size = int(os.getenv("MICKTRACE_QUEUE_SIZE", "10000"))

        # Sampling
        sampling_rate = os.getenv("MICKTRACE_SAMPLING_RATE")
        if sampling_rate:
            config.sampling.rate = float(sampling_rate)
            config.sampling.enabled = config.sampling.rate < 1.0

        config.is_configured = True
        return config

    def save_to_file(self, path: Union[str, Path]) -> None:
        """Save configuration to file."""
        path = Path(path)
        data = self.to_dict()

        if path.suffix == ".json":
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")

    @classmethod
    def load_from_file(cls, path: Union[str, Path]) -> "Configuration":
        """Load configuration from file."""
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        if path.suffix == ".json":
            with open(path, "r") as f:
                data = json.load(f)
                return cls.from_dict(data)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")


def get_configuration() -> Configuration:
    """Get the global configuration instance."""
    global _global_config

    with _config_lock:
        if _global_config is None:
            # Try to load from environment first
            try:
                _global_config = Configuration.from_env()
            except Exception:
                # Fallback to default configuration
                _global_config = Configuration()

        return _global_config


def set_configuration(config: Configuration) -> None:
    """Set the global configuration."""
    global _global_config

    with _config_lock:
        config.validate()
        config.is_configured = True
        _global_config = config


def configure(**kwargs: Any) -> None:
    """Configure micktrace programmatically."""
    current_config = get_configuration()

    # Create new configuration from current + overrides
    config_dict = current_config.to_dict()

    # Handle simple overrides
    if "level" in kwargs:
        config_dict["level"] = kwargs["level"]
    if "format" in kwargs:
        config_dict["format"] = kwargs["format"]
    if "enabled" in kwargs:
        config_dict["enabled"] = kwargs["enabled"]

    # Handle handler configuration
    if "handlers" in kwargs:
        handlers = kwargs["handlers"]
        if isinstance(handlers, str):
            # Simple string like "console,file"
            handler_types = [h.strip() for h in handlers.split(",")]
            config_dict["handlers"] = [{"type": h} for h in handler_types]
        elif isinstance(handlers, list):
            if all(isinstance(h, str) for h in handlers):
                # List of strings
                config_dict["handlers"] = [{"type": h} for h in handlers]
            else:
                # List of dicts
                config_dict["handlers"] = handlers

    # Handle context
    if "context" in kwargs or any(k in kwargs for k in ["service", "version", "environment"]):
        if "context" not in config_dict:
            config_dict["context"] = {}

        for key in ["service", "version", "environment"]:
            if key in kwargs:
                config_dict["context"][key] = kwargs[key]

        if "context" in kwargs:
            config_dict["context"].update(kwargs["context"])

    # Create and set new configuration
    new_config = Configuration.from_dict(config_dict)
    set_configuration(new_config)


def reset_configuration() -> None:
    """Reset configuration to defaults."""
    global _global_config

    with _config_lock:
        _global_config = Configuration()
