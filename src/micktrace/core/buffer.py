"""Advanced log buffering and compression for micktrace."""

import asyncio
import gzip
import json
import time
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor

from ..types import LogRecord


@dataclass
class BufferMetrics:
    """Metrics for a buffer partition."""

    total_records: int = 0
    total_bytes: int = 0
    compression_ratio: float = 0.0
    last_flush_time: float = 0.0
    avg_record_size: float = 0.0


@dataclass
class BufferPartition:
    """A partition in the buffer for efficient storage and compression."""

    records: List[LogRecord] = field(default_factory=list)
    metrics: BufferMetrics = field(default_factory=BufferMetrics)
    compressed_data: Optional[bytes] = None
    lock: threading.Lock = field(default_factory=threading.Lock)


class SmartBuffer:
    """Smart buffer with adaptive compression and partitioning."""

    def __init__(
        self,
        max_size: int = 1000000,  # 1M records total
        max_partition_size: int = 100000,  # 100K records per partition
        compression_threshold: int = 1000,  # Start compressing at 1K records
        max_age: float = 300.0,  # 5 minutes
        compression_level: int = 6,  # GZIP level 6 (good balance)
        worker_threads: int = 4,
    ):
        """Initialize the smart buffer.

        Args:
            max_size: Maximum total records in buffer
            max_partition_size: Maximum records per partition
            compression_threshold: Records before compression
            max_age: Maximum age of records before flush
            compression_level: GZIP compression level (1-9)
            worker_threads: Number of compression worker threads
        """
        self.max_size = max_size
        self.max_partition_size = max_partition_size
        self.compression_threshold = compression_threshold
        self.max_age = max_age
        self.compression_level = compression_level

        # Initialize partitions
        self._partitions: Dict[str, BufferPartition] = defaultdict(
            BufferPartition)
        self._active_partition = "default"
        self._partition_lock = threading.Lock()

        # Compression thread pool
        self._executor = ThreadPoolExecutor(max_workers=worker_threads)
        self._compress_queue: asyncio.Queue[str] = asyncio.Queue()
        self._stop_event = threading.Event()

        # Start background tasks
        self._start_background_tasks()

    def _start_background_tasks(self) -> None:
        """Start background compression and maintenance tasks."""
        self._maintenance_thread = threading.Thread(
            target=self._maintenance_loop, daemon=True
        )
        self._maintenance_thread.start()

    def _maintenance_loop(self) -> None:
        """Background loop for buffer maintenance."""
        while not self._stop_event.is_set():
            try:
                self._check_compression_needed()
                self._check_age_flush()
                time.sleep(1.0)  # Check every second
            except Exception as e:
                print(f"Error in buffer maintenance: {e}")

    def _should_compress(self, partition: BufferPartition) -> bool:
        """Check if a partition should be compressed."""
        return (
            len(partition.records) >= self.compression_threshold
            and partition.compressed_data is None
        )

    def _compress_partition(self, partition_id: str) -> None:
        """Compress a partition's records."""
        partition = self._partitions[partition_id]
        with partition.lock:
            if not self._should_compress(partition):
                return

            # Convert records to JSON for compression
            json_data = json.dumps(
                [record.__dict__ for record in partition.records]
            ).encode("utf-8")

            # Compress with GZIP
            compressed = gzip.compress(
                json_data, compresslevel=self.compression_level)

            # Update metrics
            partition.metrics.compression_ratio = len(
                compressed) / len(json_data)
            partition.metrics.total_bytes = len(compressed)
            partition.compressed_data = compressed

    def _check_compression_needed(self) -> None:
        """Check and initiate compression for eligible partitions."""
        for partition_id, partition in self._partitions.items():
            if self._should_compress(partition):
                self._executor.submit(self._compress_partition, partition_id)

    def _check_age_flush(self) -> None:
        """Check for and flush old partitions."""
        current_time = time.time()
        to_flush: Set[str] = set()

        for partition_id, partition in self._partitions.items():
            if partition.metrics.last_flush_time == 0:
                partition.metrics.last_flush_time = current_time
            elif current_time - partition.metrics.last_flush_time >= self.max_age:
                to_flush.add(partition_id)

        for partition_id in to_flush:
            self.flush_partition(partition_id)

    def add_record(self, record: LogRecord, partition_id: str = None) -> None:
        """Add a record to the buffer.

        Args:
            record: LogRecord to add
            partition_id: Optional partition ID for custom routing
        """
        if partition_id is None:
            partition_id = self._active_partition

        partition = self._partitions[partition_id]

        with partition.lock:
            # Check if current partition is full
            if len(partition.records) >= self.max_partition_size:
                # Create new partition
                with self._partition_lock:
                    new_id = f"{partition_id}_{int(time.time())}"
                    self._active_partition = new_id
                    partition = self._partitions[new_id]

            # Add record and update metrics
            partition.records.append(record)
            partition.metrics.total_records += 1
            partition.metrics.avg_record_size = (
                len(json.dumps(record.__dict__).encode("utf-8"))
                + partition.metrics.avg_record_size
                * (partition.metrics.total_records - 1)
            ) / partition.metrics.total_records

            # Update last flush time
            if partition.metrics.last_flush_time == 0:
                partition.metrics.last_flush_time = time.time()

    def get_records(
        self, partition_id: str = None, decompress: bool = True
    ) -> List[LogRecord]:
        """Get records from a partition.

        Args:
            partition_id: Partition to get records from
            decompress: Whether to decompress compressed records

        Returns:
            List of LogRecords
        """
        if partition_id is None:
            partition_id = self._active_partition

        partition = self._partitions[partition_id]
        with partition.lock:
            if partition.compressed_data and decompress:
                # Decompress and reconstruct records
                json_data = gzip.decompress(
                    partition.compressed_data).decode("utf-8")
                records_data = json.loads(json_data)
                return [LogRecord(**data) for data in records_data]
            return partition.records.copy()

    def flush_partition(self, partition_id: str) -> List[LogRecord]:
        """Flush a partition and return its records.

        Args:
            partition_id: Partition to flush

        Returns:
            List of flushed LogRecords
        """
        records = self.get_records(partition_id)
        with self._partition_lock:
            if partition_id in self._partitions:
                del self._partitions[partition_id]
        return records

    def flush_all(self) -> Dict[str, List[LogRecord]]:
        """Flush all partitions.

        Returns:
            Dict mapping partition IDs to their records
        """
        flushed = {}
        partition_ids = list(self._partitions.keys())
        for partition_id in partition_ids:
            flushed[partition_id] = self.flush_partition(partition_id)
        return flushed

    def shutdown(self) -> None:
        """Shutdown the buffer and its worker threads."""
        self._stop_event.set()
        if self._maintenance_thread.is_alive():
            self._maintenance_thread.join(timeout=5.0)
        self._executor.shutdown(wait=True)
