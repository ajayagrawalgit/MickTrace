"""
MusicStream Service - Production-Grade Logging Implementation
==========================================================

This example demonstrates how to implement comprehensive production-level logging
in a music streaming service using micktrace. While micktrace is incredibly easy
to use, this example shows how to leverage its full power for production systems.

Key Features Demonstrated:
- Massive log generation (100,000+ entries)
- All log levels (DEBUG through CRITICAL)
- Structured contextual logging
- Performance tracking
- Rich metadata and context
"""

import asyncio
import functools
import os
import random
import sys
import time
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

# Import micktrace components
import micktrace
from micktrace.handlers import FileHandler
from micktrace.types import LogLevel

# Basic service configuration
SERVICE_NAME = "MusicStream"
SERVICE_VERSION = "2.0.0"
ENVIRONMENT = "production"
SIMULATION_SIZE = 100  # Number of events to simulate
LOG_FILE = Path("logs") / "music_stream.log"

# Create log directory if it doesn't exist
LOG_FILE.parent.mkdir(exist_ok=True)

# Configure micktrace for production use
micktrace.configure(
    level="INFO",  # Set minimum level to INFO for production
    format="structured",
    service=SERVICE_NAME,
    version=SERVICE_VERSION,
    environment=ENVIRONMENT,
    handlers=[
        {
            "type": "file",
            "level": "INFO",  # Only log INFO and above to file
            "format": "structured",
            "config": {
                "path": str(LOG_FILE)
            }
        }
    ],
    enabled=True
)

@dataclass
class Track:
    """Represents a music track."""
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    artist: str = ""
    album: str = ""
    duration: float = 0.0  # in seconds
    bitrate: int = 320  # kbps
    
    def to_dict(self) -> dict:
        """Convert to dictionary for structured logging."""
        return {
            "id": str(self.id),
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "duration": self.duration,
            "bitrate": self.bitrate
        }

@dataclass
class StreamingSession:
    """Represents an active streaming session."""
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    track: Track = None
    start_time: float = field(default_factory=time.time)
    quality: str = "HIGH"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for structured logging."""
        return {
            "session_id": str(self.id),
            "user_id": str(self.user_id),
            "track": self.track.to_dict() if self.track else None,
            "duration": time.time() - self.start_time if self.start_time else 0,
            "quality": self.quality
        }

def setup_logging() -> micktrace.Logger:
    """Configure production-grade logging.
    
    This shows how easy it is to set up comprehensive logging with micktrace.
    Just create a logger, add handlers, and you're ready to go!
    """
    # Create log directory
    LOG_FILE.parent.mkdir(exist_ok=True)
    
    # Ensure all debug logging is disabled first
    os.environ["PYTHON_DEBUG"] = "0"
    os.environ["PYTHONDEBUG"] = "0"
    os.environ["DEBUG"] = "0"
    
    # First disable all logging and clear handlers
    micktrace.disable()  # Ensure everything is off
    
    # Clear handlers from root and service loggers
    root_logger = micktrace.get_logger("")
    root_logger.clear_handlers()
    
    service_logger = micktrace.get_logger(SERVICE_NAME)
    service_logger.clear_handlers()
    
    # Configure once with only file handler
    micktrace.configure(
        enabled=True,
        level="INFO",
        format="structured",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        environment=ENVIRONMENT,
        handlers=[{
            "type": "file", 
            "level": "INFO",
            "config": {"path": str(LOG_FILE)}
        }]
    )
    
    # Create the logger - it will use the configured handlers
    logger = micktrace.get_logger(SERVICE_NAME)
    
    # Log startup information with rich context
    logger.info("Music streaming service starting", data={
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "environment": ENVIRONMENT,
        "log_file": str(LOG_FILE),
        "start_time": time.time(),
        "python_version": sys.version,
        "platform": sys.platform
    })
    
    return logger

def track_performance(logger: micktrace.Logger):
    """Decorator for performance monitoring.
    
    Shows how easy it is to add performance tracking to any function!
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log performance metrics to file
                logger.debug(
                    f"Operation timing: {func.__name__}",
                    data={
                        "function": func.__name__,
                        "duration": duration,
                        "success": True
                    }
                )
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Operation failed: {func.__name__}",
                    data={
                        "function": func.__name__,
                        "duration": duration,
                        "error_type": type(e).__name__
                    },
                    exc_info=e
                )
                raise
        return wrapper
    return decorator

class MusicStreamingService:
    """Main streaming service implementation."""
    
    # Simulated events for massive log generation
    EVENTS = [
        "stream.start", "stream.buffer", "stream.pause", "stream.resume", "stream.stop",
        "playlist.create", "playlist.add", "playlist.remove", "playlist.shuffle",
        "cache.hit", "cache.miss", "cache.update", "cache.evict",
        "network.connect", "network.disconnect", "network.latency", "network.bandwidth",
        "auth.login", "auth.logout", "auth.refresh", "auth.failed",
        "metrics.cpu", "metrics.memory", "metrics.disk", "metrics.network",
        "recommendation.generate", "recommendation.serve", "recommendation.feedback"
    ]
    
    # Event severities for log levels
    EVENT_LEVELS = {
        "error": ["auth.failed", "network.disconnect"],
        "warning": ["cache.miss", "network.latency"],
        "info": ["stream.start", "stream.stop", "auth.login", "auth.logout"],
        "debug": ["cache.hit", "metrics.cpu", "stream.buffer"]
    }
    
    # Random user agents for realism
    USER_AGENTS = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (X11; Linux x86_64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Spotify/8.6.4 iOS/14.4 (iPhone12,1)",
        "MusicStream/2.0.0 Android/11"
    ]
    
    def __init__(self):
        """Initialize the service with logging."""
        self.logger = setup_logging()
        self.active_sessions: List[StreamingSession] = []
        
        # Demo tracks (in real world, from database)
        self.tracks = [
            Track(
                title="Bohemian Rhapsody",
                artist="Queen",
                album="A Night at the Opera",
                duration=354.0
            ),
            Track(
                title="Stairway to Heaven",
                artist="Led Zeppelin",
                album="Led Zeppelin IV",
                duration=482.0
            ),
            Track(
                title="Hotel California",
                artist="Eagles",
                album="Hotel California",
                duration=391.0
            )
        ]
    
    def generate_random_metrics(self) -> Dict[str, Any]:
        """Generate realistic-looking metrics."""
        return {
            "cpu_usage": round(random.uniform(10, 95), 2),
            "memory_used": round(random.uniform(100, 4096), 2),
            "network_latency": round(random.uniform(10, 200), 2),
            "active_streams": random.randint(1000, 10000),
            "cache_size": round(random.uniform(100, 1024), 2),
            "errors_last_min": random.randint(0, 10),
            "requests_per_sec": random.randint(100, 1000)
        }
    
    def get_log_level(self, event: str) -> str:
        """Determine log level for an event."""
        for level, events in self.EVENT_LEVELS.items():
            if event in events:
                return level
        return "info"  # Default level
    
    @track_performance(micktrace.get_logger(SERVICE_NAME))
    async def simulate_massive_load(self, events_count: int = SIMULATION_SIZE):
        """Simulate massive service load with comprehensive logging."""
        start_time = time.time()
        
        # Track some stats
        stats = {
            "events_processed": 0,
            "errors": 0,
            "warnings": 0,
            "start_time": start_time
        }
        
        try:
            # Generate massive amounts of events
            for i in range(events_count):
                # Generate random event data
                event = random.choice(self.EVENTS)
                user_id = str(uuid4())
                session_id = str(uuid4())
                
                # Get appropriate log level
                level = self.get_log_level(event)
                
                # Generate rich context
                context = {
                    "event": event,
                    "user_id": user_id,
                    "session_id": session_id,
                    "user_agent": random.choice(self.USER_AGENTS),
                    "client_ip": f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
                    "timestamp": time.time(),
                    "metrics": self.generate_random_metrics()
                }
                
                # Log with appropriate level
                if level == "error":
                    self.logger.error(f"Error processing {event}", data=context)
                    stats["errors"] += 1
                elif level == "warning":
                    self.logger.warning(f"Warning during {event}", data=context)
                    stats["warnings"] += 1
                elif level == "debug":
                    self.logger.debug(f"Debug info for {event}", data=context)
                else:
                    self.logger.info(f"Event processed: {event}", data=context)
                
                stats["events_processed"] += 1
                
                # Optional progress update every 10,000 events
                if (i + 1) % 10_000 == 0:
                    duration = time.time() - start_time
                    rate = (i + 1) / duration
            
            # Calculate final statistics
            duration = time.time() - start_time
            rate = events_count / duration
            
            stats.update({
                "duration": duration,
                "events_per_second": rate,
                "end_time": time.time()
            })
            
            # Log completion with full statistics
            self.logger.info(
                "Simulation completed",
                data=stats
            )
            
            pass  # Let the logs show completion
            
        except Exception as e:
            # Log critical error
            self.logger.critical(
                "Simulation failed",
                data={"error_type": type(e).__name__},
                exc_info=e
            )
            
            pass  # Error will be in the logs
            raise
            
        finally:
            # Log shutdown
            self.logger.info("Music streaming service shutting down")

async def main():
    """Main entry point showing how simple it is to use micktrace."""
    service = MusicStreamingService()
    await service.simulate_massive_load()

if __name__ == "__main__":
    asyncio.run(main())