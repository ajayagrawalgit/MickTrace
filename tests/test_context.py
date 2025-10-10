"""
Test context management functionality.
Tests sync/async context propagation, context managers, and bound loggers.
"""

import asyncio
import pytest
import micktrace


class TestContextManagement:
    """Test context management functionality."""

    def setup_method(self):
        """Setup for each test."""
        micktrace.clear_context()
        micktrace.configure(level="DEBUG", handlers=[{"type": "memory"}])

    def test_get_context_empty(self):
        """Test getting empty context."""
        ctx = micktrace.get_context()
        assert isinstance(ctx, dict)
        assert len(ctx) == 0

    def test_set_get_context(self):
        """Test setting and getting context."""
        test_data = {"user_id": 123, "action": "test"}
        micktrace.set_context(test_data)

        ctx = micktrace.get_context()
        assert ctx["user_id"] == 123
        assert ctx["action"] == "test"

    def test_context_isolation(self):
        """Test that context changes don't affect original data."""
        original_data = {"user_id": 123}
        micktrace.set_context(original_data)

        # Modify the original data
        original_data["user_id"] = 456

        # Context should still have original value
        ctx = micktrace.get_context()
        assert ctx["user_id"] == 123

    def test_clear_context(self):
        """Test clearing context."""
        micktrace.set_context({"test": "value"})
        assert len(micktrace.get_context()) > 0

        micktrace.clear_context()
        ctx = micktrace.get_context()
        assert len(ctx) == 0

    def test_context_manager(self):
        """Test context manager functionality."""
        # Start with empty context
        assert len(micktrace.get_context()) == 0

        with micktrace.context(user_id=123, action="test"):
            ctx = micktrace.get_context()
            assert ctx["user_id"] == 123
            assert ctx["action"] == "test"

        # Context should be cleared after with block
        ctx = micktrace.get_context()
        assert "user_id" not in ctx
        assert "action" not in ctx

    def test_nested_context_managers(self):
        """Test nested context managers."""
        with micktrace.context(level1="outer"):
            assert micktrace.get_context()["level1"] == "outer"

            with micktrace.context(level2="inner"):
                ctx = micktrace.get_context()
                assert ctx["level1"] == "outer"
                assert ctx["level2"] == "inner"

            # Inner context should be cleared
            ctx = micktrace.get_context()
            assert ctx["level1"] == "outer"
            assert "level2" not in ctx

    def test_correlation_context_manager(self):
        """Test correlation ID context manager."""
        with micktrace.correlation(service="test") as correlation_id:
            assert correlation_id is not None
            assert len(correlation_id) > 0

            ctx = micktrace.get_context()
            assert ctx["correlation_id"] == correlation_id
            assert ctx["service"] == "test"

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager."""
        async with micktrace.acontext(request_id="async_123"):
            ctx = micktrace.get_context()
            assert ctx["request_id"] == "async_123"

            # Test that context propagates to nested async function
            await self._nested_async_function()

    @pytest.mark.asyncio
    async def test_async_correlation(self):
        """Test async correlation ID generation."""
        async with micktrace.acorrelation(service="async_test") as correlation_id:
            assert correlation_id is not None
            ctx = micktrace.get_context()
            assert ctx["correlation_id"] == correlation_id
            assert ctx["service"] == "async_test"

    @pytest.mark.asyncio
    async def test_concurrent_async_contexts(self):
        """Test that concurrent async operations maintain separate contexts."""
        results = await asyncio.gather(
            self._async_operation("task1", 1),
            self._async_operation("task2", 2),
            self._async_operation("task3", 3),
        )

        # Each task should have maintained its own context
        assert results[0] == 1
        assert results[1] == 2
        assert results[2] == 3

    async def _nested_async_function(self):
        """Helper function to test async context propagation."""
        ctx = micktrace.get_context()
        assert ctx["request_id"] == "async_123"

    async def _async_operation(self, task_name: str, task_id: int) -> int:
        """Helper function for concurrent context testing."""
        async with micktrace.acontext(task_name=task_name, task_id=task_id):
            await asyncio.sleep(0.01)  # Simulate async work
            ctx = micktrace.get_context()
            return ctx["task_id"]


class TestBoundLoggers:
    """Test bound logger functionality with context."""

    def setup_method(self):
        """Setup for each test."""
        micktrace.clear_context()
        micktrace.configure(level="DEBUG", handlers=[{"type": "memory"}])

    def test_bound_logger_creation(self):
        """Test creating bound loggers."""
        logger = micktrace.get_logger("test")
        bound = logger.bind(service="test", version="1.0")

        assert bound is not None
        assert bound != logger

    def test_bound_logger_chaining(self):
        """Test chaining bound loggers."""
        logger = micktrace.get_logger("test")
        bound1 = logger.bind(service="test")
        bound2 = bound1.bind(version="1.0")
        bound3 = bound2.bind(request_id="req_123")

        assert bound3 is not None
        # Each binding should create a new logger instance
        assert bound1 != bound2 != bound3

    def test_bound_logger_with_context(self):
        """Test bound logger with context manager."""
        logger = micktrace.get_logger("test")
        bound = logger.bind(service="test")

        with micktrace.context(user_id=123):
            # Both bound context and context manager should be available
            bound.info("Test message")
            # This test verifies the message is logged successfully
            # In a real test, you'd capture and verify the log content
