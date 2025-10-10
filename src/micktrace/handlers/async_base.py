"""Async base handler and utilities for MickTrace."""

import asyncio
import threading
import time
import queue
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..types import LogRecord


class AsyncHandler(ABC):
    """Base class for asynchronous handlers with background worker."""

    def __init__(
        self,
        batch_size: int = 100,
        flush_interval: float = 5.0,
        max_queue_size: int = 10000,
        worker_count: int = 1,
        shutdown_timeout: float = 30.0,
    ):
        """Initialize the async handler.

        Args:
            batch_size: Maximum number of records to batch before processing
            flush_interval: Maximum seconds between flushes
            max_queue_size: Maximum number of records to queue
            worker_count: Number of background workers
            shutdown_timeout: Maximum seconds to wait for shutdown
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_queue_size = max_queue_size
        self.worker_count = worker_count
        self.shutdown_timeout = shutdown_timeout

        # Initialize queue and worker state
        self._queue: queue.Queue[Optional[LogRecord]] = queue.Queue(
            maxsize=max_queue_size
        )
        self._stop_event = threading.Event()
        self._workers: List[threading.Thread] = []
        self._last_error_time = 0
        self._error_count = 0
        self._batch: List[LogRecord] = []

        # Start workers
        self._start_workers()

    def _start_workers(self) -> None:
        """Start background worker threads."""
        for _ in range(self.worker_count):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self._workers.append(worker)

    def handle(self, record: LogRecord) -> None:
        """Handle a log record asynchronously."""
        try:
            # Don't block indefinitely if queue is full
            self._queue.put(record, timeout=1.0)
        except queue.Full:
            # Log warning about dropped records
            print(f"Warning: Dropped log record due to full queue: {record.message}")

    def _should_flush(self, batch: List[LogRecord]) -> bool:
        """Check if we should flush the current batch."""
        return len(batch) >= self.batch_size or (
            batch and time.time() - batch[0].timestamp >= self.flush_interval
        )

    def _worker_loop(self) -> None:
        """Main worker loop that processes records."""
        batch: List[LogRecord] = []
        last_flush = time.time()

        while not self._stop_event.is_set():
            try:
                # Get next record with timeout to check stop event periodically
                try:
                    record = self._queue.get(timeout=0.1)
                except queue.Empty:
                    # Check if we should flush on timeout
                    if batch and time.time() - last_flush >= self.flush_interval:
                        self._flush_batch(batch)
                        batch = []
                        last_flush = time.time()
                    continue

                # None is a signal to stop
                if record is None:
                    break

                # Add to batch
                batch.append(record)

                # Check if we should flush
                if self._should_flush(batch):
                    self._flush_batch(batch)
                    batch = []
                    last_flush = time.time()

            except Exception as e:
                self._handle_worker_error(e)

        # Final flush on shutdown
        if batch:
            try:
                self._flush_batch(batch)
            except Exception as e:
                self._handle_worker_error(e)

    def _handle_worker_error(self, error: Exception) -> None:
        """Handle worker errors with exponential backoff."""
        current_time = time.time()

        if current_time - self._last_error_time > 60:
            # Reset error count after a minute of success
            self._error_count = 0

        self._error_count += 1
        self._last_error_time = current_time

        # Calculate backoff time (exponential with max of 5 minutes)
        backoff = min(300, 2**self._error_count)

        time.sleep(backoff)

    @abstractmethod
    def _flush_batch(self, batch: List[LogRecord]) -> None:
        """Flush a batch of records. Must be implemented by subclasses."""
        raise NotImplementedError

    def flush(self) -> None:
        """Flush any buffered records."""
        # Signal workers to flush
        for _ in range(self.worker_count):
            try:
                self._queue.put(None, timeout=1.0)
            except queue.Full:
                pass

        # Wait for workers to complete
        for worker in self._workers:
            worker.join(timeout=self.shutdown_timeout / self.worker_count)

    def shutdown(self) -> None:
        """Shut down the handler, flushing any remaining records."""
        self._stop_event.set()

        # Signal workers to stop
        for _ in range(self.worker_count):
            try:
                self._queue.put(None, timeout=1.0)
            except queue.Full:
                pass

        # Wait for workers with timeout
        shutdown_start = time.time()
        for worker in self._workers:
            remaining_time = max(
                0, self.shutdown_timeout - (time.time() - shutdown_start)
            )
            worker.join(timeout=remaining_time / len(self._workers))

        self._workers.clear()


class AsyncBatchHandler(AsyncHandler):
    """Base class for handlers that process records in batches."""

    @abstractmethod
    async def process_batch(self, batch: List[LogRecord]) -> None:
        """Process a batch of records asynchronously."""
        raise NotImplementedError

    def _flush_batch(self, batch: List[LogRecord]) -> None:
        """Run async batch processing in the event loop."""
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.process_batch(batch))
        finally:
            loop.close()
            asyncio.set_event_loop(None)
