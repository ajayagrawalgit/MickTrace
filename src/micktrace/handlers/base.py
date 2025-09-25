"""
Base Handler Classes

Defines the interface for all micktrace handlers with async support,
batching, filtering, and error handling.
"""

import asyncio
import logging
import time
import threading
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from ..core.record import LogRecord
from ..filters.base import Filter
from ..formatters.base import Formatter


class HandlerState(Enum):
    """Handler state enumeration."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class Handler(ABC):
    """
    Base class for all micktrace handlers.

    Features:
    - Async-native with sync fallback
    - Built-in batching and queuing
    - Automatic error handling and retries
    - Circuit breaker pattern
    - Performance monitoring
    """

    def __init__(
        self,
        name: str,
        level: str = "INFO",
        formatter: Optional[Formatter] = None,
        filters: Optional[List[Filter]] = None,
        **kwargs: Any
    ) -> None:
        self.name = name
        self.level = level
        self.formatter = formatter
        self.filters = filters or []
        self.config = kwargs

        # State management
        self._state = HandlerState.STOPPED
        self._state_lock = threading.RLock()

        # Performance tracking
        self._records_processed = 0
        self._records_dropped = 0
        self._errors = 0
        self._last_error: Optional[Exception] = None
        self._start_time = time.time()

        # Async support
        self._queue: Optional[asyncio.Queue] = None
        self._worker_task: Optional[asyncio.Task] = None

        # Batching configuration
        self.batch_size = kwargs.get("batch_size", 1)
        self.flush_interval = kwargs.get("flush_interval", 1.0)
        self.max_queue_size = kwargs.get("max_queue_size", 10000)

        # Circuit breaker
        self.error_threshold = kwargs.get("error_threshold", 5)
        self.recovery_timeout = kwargs.get("recovery_timeout", 60.0)
        self._circuit_breaker_open = False
        self._circuit_breaker_last_failure = 0.0

    @property
    def state(self) -> HandlerState:
        """Get current handler state."""
        with self._state_lock:
            return self._state

    def _set_state(self, state: HandlerState) -> None:
        """Set handler state."""
        with self._state_lock:
            old_state = self._state
            self._state = state
            self._on_state_change(old_state, state)

    def _on_state_change(self, old_state: HandlerState, new_state: HandlerState) -> None:
        """Called when handler state changes."""
        pass  # Override in subclasses if needed

    def should_handle(self, record: LogRecord) -> bool:
        """Check if this handler should process the record."""
        # Check circuit breaker
        if self._circuit_breaker_open:
            if time.time() - self._circuit_breaker_last_failure > self.recovery_timeout:
                self._circuit_breaker_open = False
            else:
                return False

        # Check level
        from ..core.logger import LogLevel
        record_level = LogLevel.from_string(record.level)
        handler_level = LogLevel.from_string(self.level)

        if record_level < handler_level:
            return False

        # Check filters
        for filter_obj in self.filters:
            if not filter_obj.filter(record):
                return False

        return True

    def format_record(self, record: LogRecord) -> str:
        """Format a log record."""
        if self.formatter:
            return self.formatter.format(record)

        # Default formatting
        return f"{record.timestamp} {record.level} {record.logger_name} {record.message}"

    async def handle_async(self, record: LogRecord) -> None:
        """Handle a record asynchronously."""
        if not self.should_handle(record):
            return

        try:
            if self._queue is None:
                await self._start_async_handler()

            if self._queue.qsize() >= self.max_queue_size:
                self._records_dropped += 1
                return

            await self._queue.put(record)

        except Exception as e:
            self._handle_error(e)

    def handle_sync(self, record: LogRecord) -> None:
        """Handle a record synchronously."""
        if not self.should_handle(record):
            return

        try:
            formatted = self.format_record(record)
            self._emit_sync(formatted, record)
            self._records_processed += 1

        except Exception as e:
            self._handle_error(e)

    def handle(self, record: LogRecord) -> Optional[Awaitable[None]]:
        """Handle a record (async if possible, sync fallback)."""
        try:
            # Try async first
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return self.handle_async(record)
        except RuntimeError:
            pass

        # Fallback to sync
        self.handle_sync(record)
        return None

    async def _start_async_handler(self) -> None:
        """Start the async handler worker."""
        if self._queue is not None:
            return

        self._queue = asyncio.Queue(maxsize=self.max_queue_size)
        self._worker_task = asyncio.create_task(self._worker_loop())
        self._set_state(HandlerState.RUNNING)

    async def _worker_loop(self) -> None:
        """Main worker loop for async processing."""
        batch = []
        last_flush = time.time()

        try:
            while self._state in (HandlerState.STARTING, HandlerState.RUNNING):
                try:
                    # Wait for record with timeout
                    record = await asyncio.wait_for(
                        self._queue.get(), 
                        timeout=self.flush_interval
                    )
                    batch.append(record)

                    # Flush batch if full or timeout reached
                    current_time = time.time()
                    should_flush = (
                        len(batch) >= self.batch_size or 
                        current_time - last_flush >= self.flush_interval
                    )

                    if should_flush and batch:
                        await self._flush_batch(batch)
                        batch.clear()
                        last_flush = current_time

                except asyncio.TimeoutError:
                    # Flush any remaining records on timeout
                    if batch:
                        await self._flush_batch(batch)
                        batch.clear()
                        last_flush = time.time()

        except Exception as e:
            self._handle_error(e)
            self._set_state(HandlerState.ERROR)

        finally:
            # Flush remaining records
            if batch:
                try:
                    await self._flush_batch(batch)
                except Exception as e:
                    self._handle_error(e)

    async def _flush_batch(self, records: List[LogRecord]) -> None:
        """Flush a batch of records."""
        try:
            formatted_records = [self.format_record(record) for record in records]
            await self._emit_async(formatted_records, records)
            self._records_processed += len(records)

        except Exception as e:
            self._handle_error(e)
            self._records_dropped += len(records)

    def _handle_error(self, error: Exception) -> None:
        """Handle processing errors."""
        self._errors += 1
        self._last_error = error

        # Circuit breaker logic
        if self._errors >= self.error_threshold:
            self._circuit_breaker_open = True
            self._circuit_breaker_last_failure = time.time()

    @abstractmethod
    def _emit_sync(self, formatted: str, record: LogRecord) -> None:
        """Emit a single formatted record synchronously."""
        pass

    @abstractmethod
    async def _emit_async(self, formatted_records: List[str], records: List[LogRecord]) -> None:
        """Emit a batch of formatted records asynchronously."""
        pass

    async def start(self) -> None:
        """Start the handler."""
        if self._state != HandlerState.STOPPED:
            return

        self._set_state(HandlerState.STARTING)
        await self._start_async_handler()

    async def stop(self) -> None:
        """Stop the handler."""
        if self._state != HandlerState.RUNNING:
            return

        self._set_state(HandlerState.STOPPING)

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        self._queue = None
        self._worker_task = None
        self._set_state(HandlerState.STOPPED)

    async def flush(self) -> None:
        """Flush any pending records."""
        # This is handled automatically by the worker loop
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        uptime = time.time() - self._start_time

        return {
            "name": self.name,
            "state": self._state.value,
            "records_processed": self._records_processed,
            "records_dropped": self._records_dropped,
            "errors": self._errors,
            "uptime": uptime,
            "rate": self._records_processed / max(uptime, 1),
            "circuit_breaker_open": self._circuit_breaker_open,
            "last_error": str(self._last_error) if self._last_error else None
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name} ({self._state.value})>"


class NullHandler(Handler):
    """Handler that discards all log records."""

    def _emit_sync(self, formatted: str, record: LogRecord) -> None:
        pass

    async def _emit_async(self, formatted_records: List[str], records: List[LogRecord]) -> None:
        pass


class MemoryHandler(Handler):
    """Handler that stores log records in memory for testing."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.records: List[LogRecord] = []
        self.formatted_records: List[str] = []
        self._lock = threading.Lock()

    def _emit_sync(self, formatted: str, record: LogRecord) -> None:
        with self._lock:
            self.records.append(record)
            self.formatted_records.append(formatted)

    async def _emit_async(self, formatted_records: List[str], records: List[LogRecord]) -> None:
        with self._lock:
            self.records.extend(records)
            self.formatted_records.extend(formatted_records)

    def clear(self) -> None:
        """Clear stored records."""
        with self._lock:
            self.records.clear()
            self.formatted_records.clear()

    def get_records(self) -> List[LogRecord]:
        """Get all stored records."""
        with self._lock:
            return self.records.copy()

    def get_formatted(self) -> List[str]:
        """Get all formatted records."""
        with self._lock:
            return self.formatted_records.copy()
