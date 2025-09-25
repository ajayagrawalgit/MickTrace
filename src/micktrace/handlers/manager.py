"""
Handler Manager

Manages all handlers for a logger, providing async queue management,
load balancing, and error handling across multiple handlers.
"""

import asyncio
import threading
import weakref
from typing import Any, Dict, List, Optional, Set, Awaitable, Union

from .base import Handler, HandlerState
from ..core.record import LogRecord
from ..config.configuration import get_configuration


class HandlerManager:
    """
    Manages multiple handlers for efficient log processing.

    Features:
    - Async queue management
    - Load balancing across handlers
    - Automatic error handling and recovery
    - Performance monitoring
    - Hot-reload support
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, Handler] = {}
        self._handler_lock = threading.RLock()

        # Async support
        self._task_queue: Optional[asyncio.Queue] = None
        self._worker_tasks: List[asyncio.Task] = []
        self._running = False

        # Performance tracking
        self._records_handled = 0
        self._start_time: Optional[float] = None

        # Weak reference to avoid circular imports
        self._logger_refs: Set[weakref.ReferenceType] = set()

    def add_handler(self, handler: Handler) -> None:
        """Add a handler to the manager."""
        with self._handler_lock:
            self._handlers[handler.name] = handler

        # Start handler if manager is running
        if self._running:
            asyncio.create_task(handler.start())

    def remove_handler(self, name: str) -> None:
        """Remove a handler by name."""
        with self._handler_lock:
            handler = self._handlers.pop(name, None)
            if handler:
                asyncio.create_task(handler.stop())

    def get_handler(self, name: str) -> Optional[Handler]:
        """Get a handler by name."""
        with self._handler_lock:
            return self._handlers.get(name)

    def get_all_handlers(self) -> List[Handler]:
        """Get all handlers."""
        with self._handler_lock:
            return list(self._handlers.values())

    def handle(self, record: LogRecord) -> Optional[Awaitable[None]]:
        """Handle a log record with all applicable handlers."""
        if not self._handlers:
            return None

        # Fast path for synchronous handling
        sync_handlers = []
        async_handlers = []

        with self._handler_lock:
            for handler in self._handlers.values():
                if handler.should_handle(record):
                    if handler.state == HandlerState.RUNNING:
                        async_handlers.append(handler)
                    else:
                        sync_handlers.append(handler)

        # Handle synchronously for sync handlers
        for handler in sync_handlers:
            handler.handle_sync(record)

        # Handle asynchronously for async handlers  
        if async_handlers:
            return self._handle_async(record, async_handlers)

        return None

    async def _handle_async(self, record: LogRecord, handlers: List[Handler]) -> None:
        """Handle record with async handlers."""
        tasks = []

        for handler in handlers:
            task = handler.handle_async(record)
            if task:
                tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def start(self) -> None:
        """Start the handler manager."""
        if self._running:
            return

        self._running = True
        self._start_time = asyncio.get_event_loop().time()

        # Start all handlers
        start_tasks = []
        with self._handler_lock:
            for handler in self._handlers.values():
                start_tasks.append(handler.start())

        if start_tasks:
            await asyncio.gather(*start_tasks, return_exceptions=True)

    async def stop(self) -> None:
        """Stop the handler manager."""
        if not self._running:
            return

        self._running = False

        # Cancel worker tasks
        for task in self._worker_tasks:
            task.cancel()

        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)

        self._worker_tasks.clear()

        # Stop all handlers
        stop_tasks = []
        with self._handler_lock:
            for handler in self._handlers.values():
                stop_tasks.append(handler.stop())

        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

    async def flush(self) -> None:
        """Flush all handlers."""
        flush_tasks = []

        with self._handler_lock:
            for handler in self._handlers.values():
                flush_tasks.append(handler.flush())

        if flush_tasks:
            await asyncio.gather(*flush_tasks, return_exceptions=True)

    def reload_configuration(self) -> None:
        """Reload handler configuration from global config."""
        config = get_configuration()

        # Remove handlers not in new config
        current_names = set(self._handlers.keys())
        new_names = {h.type for h in config.handlers if h.enabled}

        for name in current_names - new_names:
            self.remove_handler(name)

        # Add/update handlers from config
        for handler_config in config.handlers:
            if not handler_config.enabled:
                continue

            # Import handler class dynamically
            handler_class = self._get_handler_class(handler_config.type)

            if handler_config.type not in self._handlers:
                # Create new handler
                handler = handler_class(
                    name=handler_config.type,
                    level=handler_config.level,
                    **handler_config.config
                )
                self.add_handler(handler)
            else:
                # Update existing handler configuration
                handler = self._handlers[handler_config.type]
                handler.level = handler_config.level
                handler.config.update(handler_config.config)

    def _get_handler_class(self, handler_type: str) -> type:
        """Get handler class by type name."""
        from .console import ConsoleHandler
        from .file import FileHandler
        from .http import HTTPHandler
        from .syslog import SyslogHandler

        handler_classes = {
            "console": ConsoleHandler,
            "file": FileHandler, 
            "http": HTTPHandler,
            "syslog": SyslogHandler,
            "null": lambda **kwargs: self._create_null_handler(**kwargs),
            "memory": lambda **kwargs: self._create_memory_handler(**kwargs)
        }

        if handler_type not in handler_classes:
            raise ValueError(f"Unknown handler type: {handler_type}")

        return handler_classes[handler_type]

    def _create_null_handler(self, **kwargs) -> Handler:
        """Create null handler."""
        from .base import NullHandler
        return NullHandler(**kwargs)

    def _create_memory_handler(self, **kwargs) -> Handler:
        """Create memory handler."""
        from .base import MemoryHandler
        return MemoryHandler(**kwargs)

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        handler_stats = {}

        with self._handler_lock:
            for name, handler in self._handlers.items():
                handler_stats[name] = handler.get_stats()

        total_processed = sum(
            stats["records_processed"] for stats in handler_stats.values()
        )
        total_dropped = sum(
            stats["records_dropped"] for stats in handler_stats.values()
        )
        total_errors = sum(
            stats["errors"] for stats in handler_stats.values()
        )

        uptime = 0.0
        if self._start_time:
            uptime = asyncio.get_event_loop().time() - self._start_time

        return {
            "running": self._running,
            "handler_count": len(self._handlers),
            "total_processed": total_processed,
            "total_dropped": total_dropped,
            "total_errors": total_errors,
            "uptime": uptime,
            "handlers": handler_stats
        }

    def __repr__(self) -> str:
        handler_names = list(self._handlers.keys())
        return f"<HandlerManager [{', '.join(handler_names)}]>"
