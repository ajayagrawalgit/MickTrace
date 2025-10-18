"""
Test performance characteristics and scalability.
Tests logging performance, memory usage, and high-volume scenarios.
"""

import asyncio
import time
import pytest
import micktrace


class TestLoggingPerformance:
    """Test logging performance characteristics."""

    def setup_method(self):
        """Setup for each test."""
        micktrace.clear_context()

    def test_null_handler_performance(self):
        """Test performance with null handler (should be very fast)."""
        micktrace.configure(level="INFO", handlers=[{"type": "null"}])

        logger = micktrace.get_logger("performance_test")

        start_time = time.time()

        # Log many messages
        for i in range(10000):
            logger.info("Performance test message", iteration=i)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete quickly (adjust threshold as needed)
        assert duration < 1.0, f"Logging took too long: {duration:.3f}s"

    def test_disabled_logging_performance(self):
        """Test performance when logging is disabled."""
        micktrace.configure(
            # Disable INFO/DEBUG logs
            level="CRITICAL", handlers=[{"type": "console"}]
        )

        logger = micktrace.get_logger("disabled_test")

        start_time = time.time()

        # These should be very fast since they're disabled
        for i in range(10000):
            logger.info("This message should be ignored", iteration=i)
            logger.debug("This debug message should be ignored", iteration=i)

        end_time = time.time()
        duration = end_time - start_time

        # Disabled logging should be extremely fast
        assert duration < 0.1, f"Disabled logging took too long: {duration:.3f}s"

    def test_structured_data_performance(self):
        """Test performance with complex structured data."""
        micktrace.configure(level="INFO", handlers=[{"type": "null"}])

        logger = micktrace.get_logger("structured_perf_test")

        # Create complex data structure
        complex_data = {
            "user": {"id": 123, "name": "Test User", "roles": ["admin", "user"]},
            "request": {
                "method": "POST",
                "url": "/api/test",
                "headers": {"content-type": "application/json"},
            },
            "metadata": {"timestamp": time.time(), "version": "1.0.0"},
        }

        start_time = time.time()

        for i in range(1000):
            logger.info("Complex structured message",
                        iteration=i, **complex_data)

        end_time = time.time()
        duration = end_time - start_time

        # Should handle complex data reasonably fast
        assert duration < 2.0, f"Structured logging took too long: {duration:.3f}s"

    def test_bound_logger_performance(self):
        """Test performance with bound loggers."""
        micktrace.configure(level="INFO", handlers=[{"type": "null"}])

        base_logger = micktrace.get_logger("bound_perf_test")
        bound_logger = base_logger.bind(
            service="test_service", version="1.0.0", environment="test"
        )

        start_time = time.time()

        for i in range(5000):
            bound_logger.info("Bound logger message", iteration=i)

        end_time = time.time()
        duration = end_time - start_time

        assert duration < 1.0, f"Bound logger performance too slow: {duration:.3f}s"

    def test_context_performance(self):
        """Test performance with context operations."""
        micktrace.configure(level="INFO", handlers=[{"type": "null"}])

        logger = micktrace.get_logger("context_perf_test")

        start_time = time.time()

        for i in range(1000):
            with micktrace.context(iteration=i, batch="performance_test"):
                logger.info("Context performance test")

        end_time = time.time()
        duration = end_time - start_time

        assert duration < 2.0, f"Context performance too slow: {duration:.3f}s"

    @pytest.mark.asyncio
    async def test_async_logging_performance(self):
        """Test async logging performance."""
        micktrace.configure(level="INFO", handlers=[{"type": "null"}])

        logger = micktrace.get_logger("async_perf_test")

        async def log_worker(worker_id: int):
            for i in range(100):
                logger.info("Async performance test",
                            worker_id=worker_id, iteration=i)

        start_time = time.time()

        # Run multiple concurrent workers
        tasks = [log_worker(i) for i in range(50)]
        await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        assert duration < 2.0, f"Async logging performance too slow: {duration:.3f}s"


class TestMemoryUsage:
    """Test memory usage characteristics."""

    def test_memory_handler_capacity(self):
        """Test memory handler with large number of messages."""
        micktrace.configure(level="INFO", handlers=[{"type": "memory"}])

        logger = micktrace.get_logger("memory_capacity_test")

        # Log many messages to test memory handling
        for i in range(1000):
            logger.info(
                "Memory capacity test",
                iteration=i,
                data={"key": f"value_{i}", "timestamp": time.time()},
            )

        # Should complete without memory issues

    def test_context_memory_cleanup(self):
        """Test that context data is properly cleaned up."""
        micktrace.configure(level="INFO", handlers=[{"type": "null"}])

        logger = micktrace.get_logger("memory_cleanup_test")

        # Create and destroy many contexts
        for i in range(1000):
            with micktrace.context(iteration=i, large_data="x" * 1000):
                logger.info("Memory cleanup test")

            # Context should be cleaned up after each iteration
            ctx = micktrace.get_context()
            assert "iteration" not in ctx
            assert "large_data" not in ctx

    @pytest.mark.asyncio
    async def test_async_context_memory_cleanup(self):
        """Test async context memory cleanup."""
        micktrace.configure(level="INFO", handlers=[{"type": "null"}])

        logger = micktrace.get_logger("async_memory_test")

        async def context_worker(worker_id: int):
            async with micktrace.acontext(worker_id=worker_id, data="x" * 1000):
                logger.info("Async memory test")

        # Create many async contexts
        tasks = [context_worker(i) for i in range(100)]
        await asyncio.gather(*tasks)

        # Context should be clean after all tasks complete
        ctx = micktrace.get_context()
        assert len(ctx) == 0


class TestScalability:
    """Test scalability under various loads."""

    def test_high_volume_logging(self):
        """Test high volume logging."""
        micktrace.configure(level="INFO", handlers=[{"type": "null"}])

        logger = micktrace.get_logger("high_volume_test")

        # Log very high volume of messages
        start_time = time.time()

        for i in range(50000):
            logger.info("High volume test", message_id=i)

        end_time = time.time()
        duration = end_time - start_time

        # Should handle high volume reasonably well
        assert duration < 5.0, f"High volume logging too slow: {duration:.3f}s"

    def test_many_loggers(self):
        """Test performance with many different loggers."""
        micktrace.configure(level="INFO", handlers=[{"type": "null"}])

        loggers = []
        for i in range(1000):
            logger = micktrace.get_logger(f"logger_{i}")
            loggers.append(logger)

        start_time = time.time()

        # Log from many different loggers
        for i, logger in enumerate(loggers):
            logger.info("Many loggers test", logger_id=i)

        end_time = time.time()
        duration = end_time - start_time

        assert duration < 2.0, f"Many loggers test too slow: {duration:.3f}s"

    @pytest.mark.asyncio
    async def test_concurrent_async_logging(self):
        """Test concurrent async logging scalability."""
        micktrace.configure(level="INFO", handlers=[{"type": "null"}])

        async def concurrent_worker(worker_id: int):
            logger = micktrace.get_logger(f"concurrent_worker_{worker_id}")

            async with micktrace.acontext(worker_id=worker_id):
                for i in range(50):
                    logger.info("Concurrent async test", iteration=i)
                    await asyncio.sleep(0.001)  # Simulate some async work

        start_time = time.time()

        # Run many concurrent workers
        tasks = [concurrent_worker(i) for i in range(100)]
        await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        # Should handle concurrent load well
        assert duration < 10.0, f"Concurrent async logging too slow: {duration:.3f}s"

    def test_deep_context_nesting(self):
        """Test performance with deeply nested contexts."""
        micktrace.configure(level="INFO", handlers=[{"type": "null"}])

        logger = micktrace.get_logger("deep_nesting_test")

        def nested_context_function(depth: int):
            if depth <= 0:
                logger.info("Deep nesting test", depth=depth)
                return

            with micktrace.context(depth=depth):
                nested_context_function(depth - 1)

        start_time = time.time()

        # Test deep nesting
        nested_context_function(100)

        end_time = time.time()
        duration = end_time - start_time

        assert duration < 1.0, f"Deep nesting too slow: {duration:.3f}s"
