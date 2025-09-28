"""
Test async functionality and context propagation.
Tests async context managers, concurrent operations, and context inheritance.
"""

import asyncio
import pytest
import micktrace


class TestAsyncFunctionality:
    """Test async logging and context functionality."""

    def setup_method(self):
        """Setup for each test."""
        micktrace.clear_context()
        micktrace.configure(
            level="DEBUG",
            handlers=[{"type": "memory"}]
        )

    @pytest.mark.asyncio
    async def test_async_logging(self):
        """Test basic async logging."""
        logger = micktrace.get_logger("async_test")
        
        async def async_operation():
            logger.info("Async operation started")
            await asyncio.sleep(0.01)
            logger.info("Async operation completed")
        
        await async_operation()
        # Test passes if no exceptions are raised

    @pytest.mark.asyncio
    async def test_async_context_propagation(self):
        """Test that context propagates across async boundaries."""
        logger = micktrace.get_logger("async_context_test")
        
        async with micktrace.acontext(request_id="async_req_123"):
            # Context should be available immediately
            ctx = micktrace.get_context()
            assert ctx["request_id"] == "async_req_123"
            
            # Context should propagate to nested async function
            await self._nested_async_operation()
            
            # Context should propagate across await boundaries
            await asyncio.sleep(0.01)
            ctx = micktrace.get_context()
            assert ctx["request_id"] == "async_req_123"

    @pytest.mark.asyncio
    async def test_concurrent_async_contexts(self):
        """Test that concurrent async operations maintain separate contexts."""
        async def worker(worker_id: int, delay: float):
            async with micktrace.acontext(worker_id=worker_id):
                await asyncio.sleep(delay)
                ctx = micktrace.get_context()
                return ctx.get("worker_id")
        
        # Run multiple concurrent workers
        tasks = [
            worker(1, 0.01),
            worker(2, 0.02),
            worker(3, 0.005)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Each worker should have maintained its own context
        assert 1 in results
        assert 2 in results
        assert 3 in results
        assert len(set(results)) == 3  # All results should be unique

    @pytest.mark.asyncio
    async def test_async_correlation_id(self):
        """Test async correlation ID generation and propagation."""
        async with micktrace.acorrelation(service="async_service") as correlation_id:
            assert correlation_id is not None
            assert len(correlation_id) > 0
            
            ctx = micktrace.get_context()
            assert ctx["correlation_id"] == correlation_id
            assert ctx["service"] == "async_service"
            
            # Test propagation to nested function
            nested_correlation = await self._get_correlation_id()
            assert nested_correlation == correlation_id

    @pytest.mark.asyncio
    async def test_async_exception_handling(self):
        """Test async exception handling with context."""
        logger = micktrace.get_logger("async_exception_test")
        
        async with micktrace.acontext(operation="test_exception"):
            try:
                await self._async_operation_that_fails()
            except ValueError as e:
                logger.exception("Async operation failed", error_type=type(e).__name__)
                # Test passes if exception is handled properly

    @pytest.mark.asyncio
    async def test_async_batch_processing(self):
        """Test async batch processing with context."""
        logger = micktrace.get_logger("batch_processor")
        
        async def process_item(item_id: int):
            async with micktrace.acontext(item_id=item_id):
                logger.info("Processing item", item_id=item_id)
                await asyncio.sleep(0.001)  # Simulate processing
                return f"processed_{item_id}"
        
        # Process multiple items concurrently
        items = range(1, 6)
        tasks = [process_item(item_id) for item_id in items]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(result.startswith("processed_") for result in results)

    @pytest.mark.asyncio
    async def test_async_context_cleanup(self):
        """Test that async context is properly cleaned up."""
        # Start with empty context
        assert len(micktrace.get_context()) == 0
        
        async with micktrace.acontext(temp_data="should_be_cleaned"):
            ctx = micktrace.get_context()
            assert ctx["temp_data"] == "should_be_cleaned"
        
        # Context should be cleaned up after async with block
        ctx = micktrace.get_context()
        assert "temp_data" not in ctx

    @pytest.mark.asyncio
    async def test_mixed_sync_async_context(self):
        """Test mixing sync and async context operations."""
        # Set context synchronously
        micktrace.set_context({"sync_data": "from_sync"})
        
        async with micktrace.acontext(async_data="from_async"):
            ctx = micktrace.get_context()
            assert ctx["sync_data"] == "from_sync"
            assert ctx["async_data"] == "from_async"
            
            # Test nested sync context manager
            with micktrace.context(nested_data="nested"):
                ctx = micktrace.get_context()
                assert ctx["sync_data"] == "from_sync"
                assert ctx["async_data"] == "from_async"
                assert ctx["nested_data"] == "nested"

    async def _nested_async_operation(self):
        """Helper function to test context propagation."""
        ctx = micktrace.get_context()
        assert ctx["request_id"] == "async_req_123"
        
        # Test further nesting
        await self._deeply_nested_async_operation()

    async def _deeply_nested_async_operation(self):
        """Helper function to test deep context propagation."""
        ctx = micktrace.get_context()
        assert ctx["request_id"] == "async_req_123"

    async def _get_correlation_id(self):
        """Helper function to get correlation ID from context."""
        ctx = micktrace.get_context()
        return ctx.get("correlation_id")

    async def _async_operation_that_fails(self):
        """Helper function that raises an exception."""
        await asyncio.sleep(0.001)
        raise ValueError("Test async exception")


class TestAsyncPerformance:
    """Test async performance and scalability."""

    def setup_method(self):
        """Setup for each test."""
        micktrace.clear_context()
        micktrace.configure(
            level="INFO",
            handlers=[{"type": "null"}]  # Use null handler for performance tests
        )

    @pytest.mark.asyncio
    async def test_high_concurrency_contexts(self):
        """Test high concurrency with many async contexts."""
        async def worker(worker_id: int):
            async with micktrace.acontext(worker_id=worker_id):
                await asyncio.sleep(0.001)
                return micktrace.get_context().get("worker_id")
        
        # Create many concurrent workers
        num_workers = 100
        tasks = [worker(i) for i in range(num_workers)]
        results = await asyncio.gather(*tasks)
        
        # All workers should complete successfully
        assert len(results) == num_workers
        assert all(isinstance(result, int) for result in results)
        assert set(results) == set(range(num_workers))

    @pytest.mark.asyncio
    async def test_async_logging_performance(self):
        """Test async logging performance under load."""
        logger = micktrace.get_logger("performance_test")
        
        async def log_worker(worker_id: int):
            async with micktrace.acontext(worker_id=worker_id):
                for i in range(10):
                    logger.info("Performance test message", 
                               worker_id=worker_id, 
                               message_id=i)
                return worker_id
        
        # Run multiple concurrent logging workers
        num_workers = 20
        tasks = [log_worker(i) for i in range(num_workers)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == num_workers
        assert set(results) == set(range(num_workers))
