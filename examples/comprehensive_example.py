#!/usr/bin/env python3
"""
Comprehensive MickTrace Example - Demonstrates ALL available features
Author: Ajay Agrawal
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

# Add src to path for running examples
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import micktrace
    from micktrace.types import LogLevel, LogRecord
    from micktrace.handlers import MemoryHandler, ConsoleHandler
    from micktrace.formatters import JSONFormatter, SimpleFormatter, LogfmtFormatter
    from micktrace.filters import LevelFilter, CallableFilter
except ImportError as e:
    print(f"Failed to import micktrace: {e}")
    sys.exit(1)

def setup_logging():
    """Configure micktrace with comprehensive settings."""
    # Create a memory handler for testing
    memory_handler = MemoryHandler("memory")
    
    # Configure with multiple handlers and formats
    micktrace.configure(
        level="DEBUG",
        format="structured",
        enabled=True,
        service="demo-service",
        version="1.0.0",
        environment="development",
        handlers=[
            {
                "type": "console",
                "level": "INFO",
                "format": "structured"
            },
            {
                "type": "memory",
                "level": "DEBUG",
                "format": "json"
            }
        ]
    )
    return memory_handler

class DemoService:
    """Demo service to show real-world logging patterns."""
    
    def __init__(self):
        self.logger = micktrace.get_logger(__name__).bind(
            service="demo-service",
            version="1.0.0"
        )
    
    def process_order(self, order_id: str, user_id: str) -> Dict[str, Any]:
        """Process an order with comprehensive logging."""
        with micktrace.context(
            order_id=order_id,
            user_id=user_id,
            correlation_id=str(uuid4())
        ):
            start_time = time.time()
            self.logger.info("Processing order started",
                           order_id=order_id,
                           user_id=user_id)
            
            try:
                # Simulate order processing
                time.sleep(0.1)  # Simulate work
                
                # Log progress with structured data
                self.logger.debug("Order validation complete",
                                validation_steps=["inventory", "payment", "shipping"],
                                duration_ms=int((time.time() - start_time) * 1000))
                
                result = {
                    "order_id": order_id,
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                }
                
                self.logger.info("Order processed successfully",
                               result=result,
                               duration_ms=int((time.time() - start_time) * 1000))
                
                return result
                
            except Exception as e:
                self.logger.exception(
                    "Order processing failed",
                    error_type=type(e).__name__,
                    duration_ms=int((time.time() - start_time) * 1000)
                )
                raise

    async def async_process_batch(self, batch_id: str, items: list) -> Dict[str, Any]:
        """Process a batch of items asynchronously."""
        async with micktrace.acontext(
            batch_id=batch_id,
            correlation_id=str(uuid4())
        ):
            start_time = time.time()
            self.logger.info("Batch processing started",
                           batch_id=batch_id,
                           item_count=len(items))
            
            try:
                # Simulate async batch processing
                await asyncio.sleep(0.2)  # Simulate async work
                
                result = {
                    "batch_id": batch_id,
                    "processed_count": len(items),
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                }
                
                self.logger.info("Batch processing completed",
                               result=result,
                               duration_ms=int((time.time() - start_time) * 1000))
                
                return result
                
            except Exception as e:
                self.logger.exception(
                    "Batch processing failed",
                    error_type=type(e).__name__,
                    duration_ms=int((time.time() - start_time) * 1000)
                )
                raise

def demonstrate_logging_features():
    """Demonstrate all logging features systematically."""
    logger = micktrace.get_logger("demo")
    
    print("\n1. Basic Logging Levels")
    print("-" * 50)
    logger.debug("Debug message with details", module="demo", line=42)
    logger.info("Info message about state", state="active")
    logger.warning("Warning about resource", usage=85, threshold=90)
    logger.error("Error in process", error_code="E123")
    logger.critical("Critical system issue", impact="high")
    
    print("\n2. Structured Data")
    print("-" * 50)
    logger.info("Complex data structure",
                user={
                    "id": "usr_123",
                    "name": "John Doe",
                    "roles": ["admin", "user"]
                },
                metadata={
                    "client_ip": "192.168.1.1",
                    "user_agent": "Mozilla/5.0"
                })
    
    print("\n3. Context Management")
    print("-" * 50)
    with micktrace.context(request_id=str(uuid4()), session="sess_123"):
        logger.info("Operation with context")
        with micktrace.context(sub_operation="validation"):
            logger.info("Nested operation")
    
    print("\n4. Bound Loggers")
    print("-" * 50)
    bound_logger = logger.bind(component="auth", version="2.0")
    bound_logger.info("Using bound logger")
    
    print("\n5. Exception Handling")
    print("-" * 50)
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.exception("Caught error",
                        error_type=type(e).__name__,
                        recoverable=True)

async def demonstrate_async_features():
    """Demonstrate async logging features."""
    print("\n6. Async Features")
    print("-" * 50)
    
    service = DemoService()
    
    try:
        # Process multiple batches
        batch_id = str(uuid4())
        items = [{"id": f"item_{i}"} for i in range(5)]
        
        result = await service.async_process_batch(batch_id, items)
        print(f"Async batch processing completed: {result}")
        
    except Exception as e:
        print(f"Error in async demonstration: {e}")

def demonstrate_performance_patterns(memory_handler: MemoryHandler):
    """Demonstrate logging patterns for performance monitoring."""
    print("\n7. Performance Monitoring")
    print("-" * 50)
    
    service = DemoService()
    
    try:
        # Process some orders
        for i in range(3):
            order_id = f"order_{i}"
            user_id = f"user_{i}"
            
            result = service.process_order(order_id, user_id)
            print(f"Order processed: {result}")
        
        # Show captured logs
        print("\nCaptured Logs:")
        for record in memory_handler.get_records():
            if "duration_ms" in str(record.data):
                print(f"- {record.message}: {record.data}")
        
    except Exception as e:
        print(f"Error in performance demonstration: {e}")

def demonstrate_formatters():
    """Demonstrate all available formatters."""
    print("\n8. Formatter Implementations")
    print("-" * 50)
    
    logger = micktrace.get_logger("formatters.demo")
    test_data = {
        "user": {"id": 123, "name": "Test User"},
        "action": "login",
        "metadata": {
            "ip": "192.168.1.1",
            "device": "mobile",
            "timestamp": datetime.now().isoformat()
        }
    }

    # JSON Formatter
    print("\nJSON Formatter Output:")
    json_formatter = JSONFormatter()
    record = LogRecord(
        timestamp=time.time(),
        level="INFO",
        logger_name=logger.name,
        message="Test JSON formatting",
        data=test_data
    )
    print(json_formatter.format(record))

    # Simple Formatter
    print("\nSimple Formatter Output:")
    simple_formatter = SimpleFormatter()
    print(simple_formatter.format(record))

    # Logfmt Formatter
    print("\nLogfmt Formatter Output:")
    logfmt_formatter = LogfmtFormatter()
    print(logfmt_formatter.format(record))

def demonstrate_log_levels_enum():
    """Demonstrate LogLevel enum functionality."""
    print("\n9. LogLevel Implementation")
    print("-" * 50)
    
    # Creating LogLevels
    print("\nCreating LogLevels:")
    levels = [
        LogLevel.NOTSET,   # 0
        LogLevel.DEBUG,    # 10
        LogLevel.INFO,     # 20
        LogLevel.WARNING,  # 30
        LogLevel.ERROR,    # 40
        LogLevel.CRITICAL  # 50
    ]
    
    for level in levels:
        print(f"Level: {level.name}, Value: {level.value}")
    
    # String to LogLevel conversion
    print("\nString to LogLevel conversion:")
    string_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    for level_str in string_levels:
        level = LogLevel.from_string(level_str)
        print(f"String '{level_str}' -> LogLevel.{level.name} (value: {level.value})")
    
    # Level comparisons
    print("\nLevel comparisons:")
    debug = LogLevel.DEBUG
    info = LogLevel.INFO
    warning = LogLevel.WARNING
    error = LogLevel.ERROR
    
    print(f"DEBUG < INFO: {debug < info}")
    print(f"INFO <= WARNING: {info <= warning}")
    print(f"ERROR > WARNING: {error > warning}")
    print(f"ERROR >= ERROR: {error >= error}")
    
    # Error handling
    print("\nError handling:")
    try:
        invalid_level = LogLevel.from_string("INVALID")
        print("This should not be printed")
    except ValueError as e:
        print(f"✓ Caught invalid level: {e}")
    
    # Practical usage example
    print("\nPractical usage example:")
    def is_error_or_higher(level: LogLevel) -> bool:
        return level >= LogLevel.ERROR
    
    test_levels = [
        LogLevel.INFO,
        LogLevel.WARNING,
        LogLevel.ERROR,
        LogLevel.CRITICAL
    ]
    
    for level in test_levels:
        print(f"Is {level.name} error or higher? {is_error_or_higher(level)}")

def demonstrate_filters():
    """Demonstrate all available filters."""
    print("\n10. Filter Implementations")
    print("-" * 50)

    logger = micktrace.get_logger("filters.demo")
    
    # Level Filter
    print("\nLevel Filter (INFO to ERROR):")
    level_filter = LevelFilter(min_level="INFO", max_level="ERROR")
    
    test_records = [
        LogRecord(time.time(), "DEBUG", logger.name, "Debug message"),
        LogRecord(time.time(), "INFO", logger.name, "Info message"),
        LogRecord(time.time(), "WARNING", logger.name, "Warning message"),
        LogRecord(time.time(), "ERROR", logger.name, "Error message"),
        LogRecord(time.time(), "CRITICAL", logger.name, "Critical message")
    ]
    
    for record in test_records:
        if level_filter.filter(record):
            print(f"Allowed: {record.level} - {record.message}")
        else:
            print(f"Filtered out: {record.level} - {record.message}")

    # Callable Filter
    print("\nCallable Filter (only errors with specific code):")
    def error_code_filter(record: LogRecord) -> bool:
        if not hasattr(record, 'data'):
            return True
        error_code = record.data.get('error_code', '')
        return error_code.startswith('E')

    callable_filter = CallableFilter(error_code_filter)
    
    test_records = [
        LogRecord(time.time(), "ERROR", logger.name, "Database error", 
                 data={"error_code": "E001"}),
        LogRecord(time.time(), "ERROR", logger.name, "Network error", 
                 data={"error_code": "N001"}),
        LogRecord(time.time(), "ERROR", logger.name, "System error", 
                 data={"error_code": "E002"})
    ]
    
    for record in test_records:
        if callable_filter.filter(record):
            print(f"Allowed: {record.message} (code: {record.data['error_code']})")
        else:
            print(f"Filtered out: {record.message} (code: {record.data['error_code']})")

def demonstrate_handlers():
    """Demonstrate handler configurations and features."""
    print("\n11. Handler Implementations")
    print("-" * 50)

    # Memory Handler with Custom Formatter
    memory_handler = MemoryHandler("test_memory_handler")
    logger = micktrace.get_logger("handlers.demo")

    # Log some messages
    logger.info("Test message 1", test_id=1)
    logger.error("Test message 2", test_id=2, error_code="E001")

    # Console Handler with Different Formatters
    console_handler = ConsoleHandler("test_console_handler")
    
    # Test with different formatters
    formatters = {
        "JSON": JSONFormatter(),
        "Simple": SimpleFormatter(),
        "Logfmt": LogfmtFormatter()
    }

    test_record = LogRecord(
        timestamp=time.time(),
        level="INFO",
        logger_name="handlers.test",
        message="Testing handlers",
        data={
            "handler": "console",
            "test": True,
            "metadata": {
                "version": "1.0.0",
                "environment": "test"
            }
        }
    )

    print("\nHandler Output with Different Formatters:")
    for name, formatter in formatters.items():
        print(f"\n{name} Formatter:")
        console_handler.emit(test_record)

def main():
    """Main function demonstrating all MickTrace features."""
    print("🚀 MickTrace Comprehensive Feature Demo")
    print("=" * 60)

    try:
        # Setup logging
        memory_handler = setup_logging()
        
        # Run synchronous demonstrations
        demonstrate_logging_features()
        demonstrate_performance_patterns(memory_handler)
        
        # Run async demonstrations
        asyncio.run(demonstrate_async_features())
        
        # Demonstrate all components
        demonstrate_formatters()
        demonstrate_log_levels_enum()
        demonstrate_filters()
        demonstrate_handlers()
        
        print("\n✅ All demonstrations completed successfully!")
        return 0

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())