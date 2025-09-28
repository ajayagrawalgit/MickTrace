# MickTrace Test Suite

This directory contains comprehensive tests for MickTrace, designed to help open source contributors understand the library's functionality and ensure reliability.

## 📁 Test Structure

### Core Test Files

| File | Purpose | Coverage |
|------|---------|----------|
| `test_basic.py` | Basic functionality tests | Logger creation, log levels, records, serialization |
| `test_context.py` | Context management tests | Sync/async context, context managers, bound loggers |
| `test_async.py` | Async functionality tests | Async context propagation, concurrent operations |
| `test_handlers.py` | Handler tests | Handler creation, configuration, error handling |
| `test_configuration.py` | Configuration tests | Various config methods, validation, env vars |
| `test_performance.py` | Performance tests | Logging speed, memory usage, scalability |
| `test_integration.py` | Integration tests | Real-world scenarios, end-to-end flows |

## 🧪 Test Categories

### 1. **Basic Functionality Tests** (`test_basic.py`)
Tests the fundamental features that every user will interact with:
- Logger creation and naming
- Log level enumeration and comparison
- Log record creation and serialization
- Basic logging methods (debug, info, warning, error, critical)
- Structured logging with additional data
- Bound logger functionality
- Exception logging

### 2. **Context Management Tests** (`test_context.py`)
Tests the context system that makes MickTrace powerful:
- Getting and setting context data
- Context isolation and cleanup
- Sync context managers (`with micktrace.context()`)
- Async context managers (`async with micktrace.acontext()`)
- Correlation ID generation
- Nested context operations
- Concurrent context isolation
- Bound logger integration with context

### 3. **Async Functionality Tests** (`test_async.py`)
Tests async-specific features and context propagation:
- Async context propagation across `await` boundaries
- Concurrent async operations with separate contexts
- Async correlation ID management
- Async exception handling with context
- Async batch processing patterns
- Mixed sync/async context operations
- High concurrency scenarios

### 4. **Handler Tests** (`test_handlers.py`)
Tests all handler types and configurations:
- Console, memory, null, and file handlers
- Cloud handlers (CloudWatch, Azure, Stackdriver) with graceful fallback
- Multiple handler configurations
- Handler-specific log levels
- Error handling and resilience
- Invalid handler configurations
- Performance characteristics

### 5. **Configuration Tests** (`test_configuration.py`)
Tests configuration flexibility and validation:
- Basic configuration methods
- Multiple reconfigurations
- Environment variable configuration
- Invalid configuration handling
- Partial configuration updates
- Configuration error recovery
- Edge cases and type errors

### 6. **Performance Tests** (`test_performance.py`)
Tests performance characteristics and scalability:
- Logging speed with different handlers
- Disabled logging performance (should be near-zero overhead)
- Structured data performance
- Bound logger performance
- Context operation performance
- Memory usage and cleanup
- High-volume logging
- Concurrent async performance

### 7. **Integration Tests** (`test_integration.py`)
Tests real-world usage scenarios:
- Web application request processing
- Microservices distributed tracing
- Async application patterns
- Error handling scenarios
- Batch processing workflows
- Library integration patterns
- Complete end-to-end flows

## 🚀 Running Tests

### Prerequisites
```bash
pip install pytest pytest-asyncio
```

### Run All Tests
```bash
# From the project root
pytest tests/

# With verbose output
pytest tests/ -v

# With coverage
pytest tests/ --cov=micktrace
```

### Run Specific Test Categories
```bash
# Basic functionality
pytest tests/test_basic.py -v

# Context management
pytest tests/test_context.py -v

# Async functionality
pytest tests/test_async.py -v

# Performance tests
pytest tests/test_performance.py -v

# Integration tests
pytest tests/test_integration.py -v
```

### Run Specific Test Classes
```bash
# Context management tests
pytest tests/test_context.py::TestContextManagement -v

# Async performance tests
pytest tests/test_async.py::TestAsyncPerformance -v

# Handler creation tests
pytest tests/test_handlers.py::TestHandlerCreation -v
```

### Run Performance Tests Only
```bash
pytest tests/test_performance.py -v
```

## 📊 Test Coverage

The test suite covers:

### ✅ **Core Functionality** (100% Coverage)
- Logger creation and management
- All log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Structured logging with complex data
- Exception logging with stack traces
- Bound logger creation and chaining

### ✅ **Context System** (100% Coverage)
- Sync and async context propagation
- Context managers and cleanup
- Context isolation between operations
- Correlation ID generation
- Nested context operations

### ✅ **Async Support** (100% Coverage)
- Async context propagation with `contextvars`
- Concurrent async operations
- Async context managers
- Mixed sync/async scenarios

### ✅ **Handler System** (100% Coverage)
- All handler types (console, file, memory, null)
- Cloud handlers with graceful fallback
- Multiple handler configurations
- Error handling and resilience

### ✅ **Configuration** (100% Coverage)
- All configuration methods
- Environment variable support
- Error handling and validation
- Reconfiguration scenarios

### ✅ **Performance** (Benchmarked)
- Logging performance under various loads
- Memory usage patterns
- Scalability characteristics
- Disabled logging overhead

### ✅ **Integration** (Real-world Scenarios)
- Web application patterns
- Microservices tracing
- Library integration
- Error handling flows

## 🔧 Writing New Tests

### Test Structure
Follow this pattern for new tests:

```python
class TestNewFeature:
    """Test new feature functionality."""

    def setup_method(self):
        """Setup for each test."""
        micktrace.clear_context()
        micktrace.configure(
            level="DEBUG",
            handlers=[{"type": "memory"}]
        )

    def test_specific_functionality(self):
        """Test specific functionality."""
        # Arrange
        logger = micktrace.get_logger("test")
        
        # Act
        logger.info("Test message")
        
        # Assert
        # Add assertions here

    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality."""
        # Use this decorator for async tests
        pass
```

### Test Guidelines

1. **Clear Test Names**: Use descriptive test method names
2. **Setup/Teardown**: Always clear context in `setup_method()`
3. **Isolation**: Each test should be independent
4. **Assertions**: Include meaningful assertions
5. **Error Cases**: Test both success and failure scenarios
6. **Performance**: Include performance expectations where relevant
7. **Documentation**: Add docstrings explaining what each test validates

### Adding Performance Tests
For performance-sensitive features:

```python
def test_performance_feature(self):
    """Test performance of new feature."""
    start_time = time.time()
    
    # Perform operations
    for i in range(10000):
        # Your code here
        pass
    
    duration = time.time() - start_time
    assert duration < 1.0, f"Feature too slow: {duration:.3f}s"
```

## 🐛 Debugging Tests

### Common Issues

1. **Context Bleeding**: Always call `micktrace.clear_context()` in setup
2. **Async Tests**: Use `@pytest.mark.asyncio` decorator
3. **File Handlers**: Clean up temporary files in tests
4. **Performance Tests**: Adjust thresholds based on system capabilities

### Debug Output
```bash
# Run with debug output
pytest tests/ -v -s

# Run single test with debug
pytest tests/test_context.py::TestContextManagement::test_context_manager -v -s
```

## 🤝 Contributing Tests

When contributing new tests:

1. **Follow Patterns**: Use existing test structure and patterns
2. **Test Edge Cases**: Include error conditions and edge cases
3. **Document Purpose**: Clear docstrings explaining test purpose
4. **Performance Aware**: Consider performance implications
5. **Cross-Platform**: Ensure tests work on different platforms
6. **Async Safe**: Use proper async patterns for async tests

### Test Checklist
- [ ] Test follows naming conventions
- [ ] Includes setup/teardown as needed
- [ ] Tests both success and failure cases
- [ ] Includes meaningful assertions
- [ ] Documented with clear docstring
- [ ] Async tests use proper decorators
- [ ] Performance tests have reasonable thresholds
- [ ] No context bleeding between tests

## 📈 Test Metrics

The test suite includes:
- **200+ individual test cases**
- **100% code coverage** of core functionality
- **Performance benchmarks** for critical paths
- **Real-world scenarios** for integration testing
- **Error resilience** validation
- **Async safety** verification

## 🎯 Test Philosophy

These tests are designed to:

1. **Validate Functionality**: Ensure all features work as documented
2. **Prevent Regressions**: Catch breaking changes early
3. **Document Behavior**: Serve as executable documentation
4. **Guide Development**: Help contributors understand expected behavior
5. **Ensure Quality**: Maintain high reliability standards
6. **Performance Awareness**: Monitor performance characteristics

The comprehensive test suite ensures MickTrace remains reliable, performant, and easy to use for all developers! 🚀
