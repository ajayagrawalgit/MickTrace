"""
Production-grade example of MickTrace implementation in a microservice environment.
This example demonstrates proper logging practices, error handling, and monitoring
in a simulated order processing service.
"""

import asyncio
import datetime
import json
import os
import uuid
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml

from micktrace import (
    LogLevel,
    LogRecord,
    acontext,
    bind,
    configure,
    get_logger,
)
from micktrace.handlers import console, handlers
from micktrace.formatters import formatters
from micktrace.filters import filters

# Initialize paths
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "logging_config.yaml"
LOGS_DIR = BASE_DIR / "logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)

class ServiceStatus:
    """Service health and status tracking."""
    OK = "healthy"
    DEGRADED = "degraded"
    ERROR = "error"


class OrderProcessingService:
    """Simulated order processing service with comprehensive logging."""

    def __init__(self):
        self.logger = get_logger("order_service")
        self.setup_logging()
        self.orders_processed = 0
        self.service_start_time = datetime.datetime.now()
        self.failed_orders = 0
        self.avg_processing_time = 0.0
        self.last_error_time = None
        self.consecutive_errors = 0
        self.status = ServiceStatus.OK
        self.health_check_interval = 30  # seconds

    def setup_logging(self) -> None:
        """Configure logging with production settings."""
        try:
            # Direct configuration setup for guaranteed file logging
            handlers_config = {
                "console": {
                    "type": "console",
                    "level": "INFO",
                    "enabled": True,
                    "format": "colorized",
                    "formatter": formatters.ColorizedFormatter(
                        timestamp_format="%Y-%m-%d %H:%M:%S",
                        include_context=True,
                        colored_level=True
                    )
                },
                "file": {
                    "type": "rotating_file",
                    "level": "DEBUG",
                    "enabled": True,
                    "format": "structured",
                    "formatter": formatters.StructuredFormatter(
                        include_timestamp=True,
                        include_level=True,
                        include_context=True
                    ),
                    "filename": str(LOGS_DIR / "service.log"),
                    "maxBytes": 10 * 1024 * 1024,  # 10MB
                    "backupCount": 5
                },
                "error_file": {
                    "type": "rotating_file",
                    "level": "ERROR",
                    "enabled": True,
                    "format": "structured",
                    "formatter": formatters.StructuredFormatter(
                        include_timestamp=True,
                        include_level=True,
                        include_context=True,
                        include_stack_trace=True
                    ),
                    "filename": str(LOGS_DIR / "error.log"),
                    "maxBytes": 10 * 1024 * 1024,  # 10MB
                    "backupCount": 5
                }
            }
            
            # Create handlers
            configured_handlers = []
            for name, config in handlers_config.items():
                if config["type"] == "console":
                    handler = console.ConsoleHandler(
                        name=name,
                        level=LogLevel.from_string(config["level"]),
                        formatter=config["formatter"]
                    )
                elif config["type"] == "rotating_file":
                    handler = handlers.RotatingFileHandler(
                        name=name,
                        level=LogLevel.from_string(config["level"]),
                        formatter=config["formatter"],
                        filename=config["filename"],
                        maxBytes=config["maxBytes"],
                        backupCount=config["backupCount"]
                    )
                else:
                    continue
                configured_handlers.append(handler)

            # Configure logging with the handlers
            configure(
                handlers=configured_handlers,
                level="DEBUG",
                environment="production",
                service="order-processing-service",
                version="1.0.0"
            )

            # Bind global context
            self.logger = bind(
                service="order-processing",
                environment="production",
                version="1.0.0"
            )

            # Log initialization
            self.logger.info(
                "Logging system initialized",
                log_dir=str(LOGS_DIR),
                handler_count=len(configured_handlers)
            )

        except Exception as e:
            # Fallback to basic console logging if configuration fails
            console_handler = console.ConsoleHandler(
                level=LogLevel.DEBUG,
                formatter=formatters.JSONFormatter(include_timestamp=True)
            )
            configure(handlers=[console_handler], default_level=LogLevel.DEBUG)
            self.logger.error(
                "Failed to initialize logging configuration",
                error=str(e),
                fallback="console_only"
            )
            raise

    async def process_order(self, order_data: Dict) -> Dict:
        """Process a single order with proper context and error handling."""
        order_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        start_time = datetime.datetime.now()
        
        async with acontext(
            order_id=order_id,
            correlation_id=correlation_id,
            user_id=order_data.get("user_id"),
            request_time=start_time.isoformat()
        ):
            try:
                self.logger.info(
                    "Starting order processing",
                    order_data=order_data
                )

                # Simulate order validation
                await self._validate_order(order_data)

                # Simulate payment processing
                await self._process_payment(order_data)

                # Simulate inventory check
                await self._check_inventory(order_data)

                # Simulate order fulfillment
                result = await self._fulfill_order(order_data)

                self.orders_processed += 1
                processing_time = (datetime.datetime.now() - start_time).total_seconds()
                
                # Update performance metrics
                self.avg_processing_time = (
                    (self.avg_processing_time * (self.orders_processed - 1) + processing_time) 
                    / self.orders_processed
                )
                self.consecutive_errors = 0  # Reset error counter on success
                
                self.logger.info(
                    "Order processed successfully",
                    order_id=order_id,
                    result=result,
                    processing_time=processing_time,
                    avg_processing_time=self.avg_processing_time
                )

                return result

            except ValueError as e:
                self.logger.error(
                    "Order validation failed",
                    error=str(e),
                    order_data=order_data
                )
                raise
            except Exception as e:
                self.failed_orders += 1
                self.consecutive_errors += 1
                self.last_error_time = datetime.datetime.now()
                
                # Update service status based on error count
                if self.consecutive_errors >= 10:
                    self.status = ServiceStatus.ERROR
                elif self.consecutive_errors >= 5:
                    self.status = ServiceStatus.DEGRADED
                
                error_context = {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "stack_trace": traceback.format_exc(),
                    "consecutive_errors": self.consecutive_errors,
                    "total_failed_orders": self.failed_orders
                }
                
                self.logger.error(
                    "Unexpected error during order processing",
                    **error_context,
                    order_data=order_data
                )
                raise

    async def _validate_order(self, order_data: Dict) -> None:
        """Validate order data with detailed logging."""
        self.logger.debug("Validating order", stage="validation")
        if not order_data.get("items"):
            raise ValueError("Order must contain items")
        await asyncio.sleep(0.1)  # Simulate validation time
        self.logger.debug(
            "Order validation complete",
            validation_result="passed"
        )

    async def _process_payment(self, order_data: Dict) -> None:
        """Process payment with error handling and logging."""
        self.logger.debug(
            "Processing payment",
            amount=order_data.get("total_amount"),
            currency=order_data.get("currency", "USD")
        )
        await asyncio.sleep(0.2)  # Simulate payment processing
        self.logger.debug("Payment processed successfully")

    async def _check_inventory(self, order_data: Dict) -> None:
        """Check inventory availability with logging."""
        self.logger.debug(
            "Checking inventory",
            items=order_data.get("items")
        )
        await asyncio.sleep(0.1)  # Simulate inventory check
        self.logger.debug("Inventory check complete")

    async def _fulfill_order(self, order_data: Dict) -> Dict:
        """Fulfill order and return result with logging."""
        self.logger.debug("Fulfilling order")
        await asyncio.sleep(0.3)  # Simulate fulfillment
        
        result = {
            "order_id": str(uuid.uuid4()),
            "status": "completed",
            "timestamp": datetime.datetime.now().isoformat(),
            "items_processed": len(order_data.get("items", [])),
            "total_amount": order_data.get("total_amount")
        }
        
        self.logger.debug(
            "Order fulfillment complete",
            fulfillment_result=result
        )
        return result

    async def process_batch(self, orders: List[Dict], max_retries: int = 3, 
                           circuit_breaker_threshold: int = 5) -> List[Dict]:
        """Process a batch of orders with retries and circuit breaker pattern."""
        batch_id = str(uuid.uuid4())
        start_time = datetime.datetime.now()
        failed_attempts = 0
        
        async with acontext(
            batch_id=batch_id,
            batch_size=len(orders)
        ):
            self.logger.info(
                "Starting batch processing",
                order_count=len(orders),
                max_retries=max_retries,
                circuit_breaker_threshold=circuit_breaker_threshold
            )
            
            results = []
            retry_queue = [(order, 0) for order in orders]  # (order, retry_count)
            
            while retry_queue:
                if failed_attempts >= circuit_breaker_threshold:
                    self.status = ServiceStatus.ERROR
                    self.logger.error(
                        "Circuit breaker triggered - stopping batch processing",
                        failed_attempts=failed_attempts,
                        remaining_orders=len(retry_queue)
                    )
                    break
                
                order, retry_count = retry_queue.pop(0)
                
                try:
                    # Add jitter to retries to prevent thundering herd
                    if retry_count > 0:
                        await asyncio.sleep(retry_count * 0.1 * (0.5 + 0.5 * uuid.uuid4().int / 2**64))
                    
                    result = await self.process_order(order)
                    results.append(result)
                    
                    # Log success after retry
                    if retry_count > 0:
                        self.logger.info(
                            "Order processed successfully after retry",
                            order_id=result.get("order_id"),
                            retry_attempt=retry_count
                        )
                    
                except Exception as e:
                    failed_attempts += 1
                    
                    if retry_count < max_retries:
                        retry_queue.append((order, retry_count + 1))
                        self.logger.warning(
                            "Retrying failed order",
                            order_data=order,
                            error=str(e),
                            retry_attempt=retry_count + 1,
                            max_retries=max_retries
                        )
                    else:
                        self.logger.error(
                            "Order processing failed after max retries",
                            order_data=order,
                            error=str(e),
                            max_retries=max_retries
                        )
            
            duration = (datetime.datetime.now() - start_time).total_seconds()
            
            # Calculate batch metrics
            total_attempted = len(orders)
            successful_orders = len(results)
            failed_orders = total_attempted - successful_orders
            retry_rate = failed_attempts / total_attempted if total_attempted > 0 else 0
            
            # Update service status based on batch metrics
            if retry_rate > 0.5:  # More than 50% retries
                self.status = ServiceStatus.DEGRADED
            
            self.logger.info(
                "Batch processing complete",
                successful_orders=successful_orders,
                failed_orders=failed_orders,
                retry_rate=f"{retry_rate:.2%}",
                total_attempts=failed_attempts + successful_orders,
                duration_seconds=duration,
                status=self.status
            )
            
            return results

    def get_service_metrics(self) -> Dict:
        """Get comprehensive service metrics for monitoring."""
        current_time = datetime.datetime.now()
        uptime = (current_time - self.service_start_time).total_seconds()
        
        metrics = {
            "service": {
                "status": self.status,
                "uptime_seconds": uptime,
                "start_time": self.service_start_time.isoformat(),
                "current_time": current_time.isoformat()
            },
            "performance": {
                "orders_processed": self.orders_processed,
                "failed_orders": self.failed_orders,
                "success_rate": (self.orders_processed - self.failed_orders) / max(self.orders_processed, 1) * 100,
                "orders_per_second": self.orders_processed / uptime if uptime > 0 else 0,
                "avg_processing_time": self.avg_processing_time
            },
            "errors": {
                "consecutive_errors": self.consecutive_errors,
                "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None
            },
            "health": {
                "status": self.get_health_status(),
                "check_interval": self.health_check_interval
            }
        }
        
        # Log metrics periodically
        self.logger.info(
            "Service metrics updated",
            metrics=metrics,
            status=self.status
        )
        
        return metrics

    def get_health_status(self) -> Dict:
        """Get detailed health status information."""
        error_threshold = 5  # Number of consecutive errors before degraded state
        critical_threshold = 10  # Number of consecutive errors before error state
        
        status = {
            "status": self.status,
            "checks": {
                "error_rate": {
                    "status": ServiceStatus.OK,
                    "message": "Error rate within acceptable limits"
                },
                "processing_time": {
                    "status": ServiceStatus.OK,
                    "message": "Processing time within normal range"
                }
            }
        }
        
        # Check error rate
        if self.consecutive_errors >= critical_threshold:
            status["checks"]["error_rate"].update({
                "status": ServiceStatus.ERROR,
                "message": f"Critical error rate: {self.consecutive_errors} consecutive errors"
            })
        elif self.consecutive_errors >= error_threshold:
            status["checks"]["error_rate"].update({
                "status": ServiceStatus.DEGRADED,
                "message": f"High error rate: {self.consecutive_errors} consecutive errors"
            })
        
        # Check processing time
        if self.avg_processing_time > 1.0:  # More than 1 second avg processing time
            status["checks"]["processing_time"].update({
                "status": ServiceStatus.DEGRADED,
                "message": f"Slow processing time: {self.avg_processing_time:.2f} seconds"
            })
        
        return status

async def monitor_service_health(service: OrderProcessingService) -> None:
    """Continuously monitor service health and metrics."""
    while True:
        try:
            health_status = service.get_health_status()
            metrics = service.get_service_metrics()
            
            # Log detailed health information
            service.logger.info(
                "Health check completed",
                health_status=health_status,
                performance_metrics=metrics["performance"],
                error_metrics=metrics["errors"]
            )
            
            # Check for warning conditions
            if health_status["status"] != ServiceStatus.OK:
                service.logger.warning(
                    "Service health degraded",
                    status=health_status["status"],
                    checks=health_status["checks"]
                )
            
        except Exception as e:
            service.logger.error(
                "Health check failed",
                error=str(e),
                stack_trace=traceback.format_exc()
            )
        
        await asyncio.sleep(service.health_check_interval)


async def cleanup_service(service: OrderProcessingService) -> None:
    """Periodic service cleanup and maintenance."""
    while True:
        try:
            # Log current service state
            service.logger.info(
                "Starting service maintenance",
                current_status=service.status,
                orders_processed=service.orders_processed,
                failed_orders=service.failed_orders
            )
            
            # Reset error counters if service has been stable
            if service.consecutive_errors > 0 and \
               (datetime.datetime.now() - service.last_error_time).total_seconds() > 300:
                old_errors = service.consecutive_errors
                service.consecutive_errors = 0
                service.status = ServiceStatus.OK
                service.logger.info(
                    "Reset error counters after stability period",
                    previous_errors=old_errors,
                    new_status=service.status
                )
            
        except Exception as e:
            service.logger.error(
                "Service maintenance failed",
                error=str(e),
                stack_trace=traceback.format_exc()
            )
        
        await asyncio.sleep(60)  # Run maintenance every minute


async def run_service_tasks(service: OrderProcessingService) -> None:
    """Run all service background tasks."""
    tasks = [
        monitor_service_health(service),
        cleanup_service(service)
    ]
    
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        service.logger.info("Service tasks cancelled")
    except Exception as e:
        service.logger.error(
            "Service tasks failed",
            error=str(e),
            stack_trace=traceback.format_exc()
        )


async def main():
    """Main function demonstrating the service usage with health monitoring."""
    try:
        service = OrderProcessingService()
        
        # Start background tasks
        background_tasks = asyncio.create_task(run_service_tasks(service))
        
        # Generate sample orders
        sample_orders = [
            {
                "user_id": f"user_{i}",
                "items": [{"id": f"item_{j}", "quantity": 1} for j in range(2)],
                "total_amount": 100.0,
                "currency": "USD",
                "priority": "high" if i % 3 == 0 else "normal"
            }
            for i in range(10)
        ]

        # Process some orders individually
        service.logger.info("Starting individual order processing")
        for order in sample_orders[:3]:
            try:
                result = await service.process_order(order)
                service.logger.info(
                    "Individual order processed",
                    order_result=result
                )
            except Exception as e:
                service.logger.error(
                    "Individual order failed",
                    error=str(e)
                )

        # Process orders in batches with different configurations
        service.logger.info("Starting batch processing tests")
        
        # Normal batch
        batch1 = await service.process_batch(
            sample_orders[3:6],
            max_retries=2,
            circuit_breaker_threshold=3
        )
        service.logger.info(
            "First batch complete",
            successful_orders=len(batch1)
        )
        
        # Batch with simulated failures (corrupted orders)
        corrupted_orders = [
            {**order, "items": None} for order in sample_orders[6:]
        ]
        batch2 = await service.process_batch(
            corrupted_orders,
            max_retries=3,
            circuit_breaker_threshold=5
        )
        service.logger.info(
            "Second batch (with failures) complete",
            successful_orders=len(batch2)
        )

        # Wait for some health checks
        service.logger.info("Monitoring service for 30 seconds...")
        await asyncio.sleep(30)
        
        # Get final service status
        metrics = service.get_service_metrics()
        health = service.get_health_status()
        
        service.logger.info(
            "Service demo complete",
            final_metrics=metrics,
            health_status=health,
            total_orders_processed=service.orders_processed,
            failure_rate=f"{(service.failed_orders / service.orders_processed):.2%}"
        )
        
        # Cancel background tasks
        background_tasks.cancel()
        try:
            await background_tasks
        except asyncio.CancelledError:
            service.logger.info("Background tasks cancelled")

    except Exception as e:
        print(f"Service demonstration failed: {e}")
        traceback.print_exc()
        raise
    finally:
        # Ensure we see the final metrics
        if 'service' in locals():
            try:
                final_metrics = service.get_service_metrics()
                print(f"\nFinal service metrics:")
                print(json.dumps(final_metrics, indent=2))
            except Exception as e:
                print(f"Failed to print final metrics: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nService stopped by user")
    except Exception as e:
        print(f"Service failed: {e}")
        traceback.print_exc()