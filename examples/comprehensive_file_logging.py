#!/usr/bin/env python3
"""
Comprehensive File Logging Example - MickTrace
==============================================

This example demonstrates comprehensive file-only logging with MickTrace,
generating 100-150 log entries across all log levels to showcase that
logs go ONLY to the file and NOT to the console.

Features demonstrated:
- File-only logging (no console output)
- All log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Structured logging with rich context
- Performance monitoring
- Error handling and exception logging
- Business logic simulation with realistic scenarios
"""

import asyncio
import random
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

# Import micktrace
import micktrace

# Configuration
SERVICE_NAME = "ComprehensiveDemo"
SERVICE_VERSION = "1.0.0"
ENVIRONMENT = "development"
LOG_FILE = Path("logs") / "comprehensive_demo.log"
TARGET_LOG_COUNT = 125  # Target number of log entries

# Create log directory
LOG_FILE.parent.mkdir(exist_ok=True)


@dataclass
class User:
    """Represents a user in our system."""

    id: str
    name: str
    email: str
    role: str = "user"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
        }


@dataclass
class Transaction:
    """Represents a financial transaction."""

    id: str
    user_id: str
    amount: float
    currency: str = "USD"
    status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
        }


class ComprehensiveLoggingDemo:
    """Comprehensive logging demonstration service."""

    def __init__(self):
        """Initialize the demo service with file-only logging."""
        self.log_count = 0  # Initialize counter first
        self.setup_logging()
        self.logger = micktrace.get_logger(SERVICE_NAME)
        self.users = self._generate_sample_users()
        self.transactions = []

        # Log service initialization
        self._log_with_count(
            "INFO",
            "Service initialized successfully",
            {
                "service": SERVICE_NAME,
                "version": SERVICE_VERSION,
                "environment": ENVIRONMENT,
                "log_file": str(LOG_FILE),
                "users_count": len(self.users),
            },
        )

    def setup_logging(self):
        """Configure file-only logging with zero console output."""
        print("🔧 Setting up file-only logging...")

        # Disable any existing logging
        micktrace.disable()

        # Configure with ONLY file handler
        micktrace.configure(
            enabled=True,
            level="DEBUG",  # Capture all levels
            format="structured",
            service=SERVICE_NAME,
            version=SERVICE_VERSION,
            environment=ENVIRONMENT,
            handlers=[
                {"type": "file", "level": "DEBUG",
                    "config": {"path": str(LOG_FILE)}}
            ],
        )

        print(f"✅ Logging configured - all logs will go to: {LOG_FILE}")
        print("🚫 NO logs should appear in console after this point!")
        print("=" * 60)

    def _log_with_count(
        self, level: str, message: str, data: Optional[Dict[str, Any]] = None
    ):
        """Log a message and increment counter."""
        self.log_count += 1
        log_data = data or {}
        log_data["log_sequence"] = self.log_count

        if level == "DEBUG":
            self.logger.debug(message, **log_data)
        elif level == "INFO":
            self.logger.info(message, **log_data)
        elif level == "WARNING":
            self.logger.warning(message, **log_data)
        elif level == "ERROR":
            self.logger.error(message, **log_data)
        elif level == "CRITICAL":
            self.logger.critical(message, **log_data)

    def _generate_sample_users(self) -> List[User]:
        """Generate sample users for the demo."""
        users = [
            User("u001", "Alice Johnson", "alice@example.com", "admin"),
            User("u002", "Bob Smith", "bob@example.com", "user"),
            User("u003", "Carol Davis", "carol@example.com", "user"),
            User("u004", "David Wilson", "david@example.com", "moderator"),
            User("u005", "Eve Brown", "eve@example.com", "user"),
        ]

        self._log_with_count(
            "DEBUG",
            "Sample users generated",
            {
                "users_generated": len(users),
                "admin_count": sum(1 for u in users if u.role == "admin"),
                "user_count": sum(1 for u in users if u.role == "user"),
                "moderator_count": sum(1 for u in users if u.role == "moderator"),
            },
        )

        return users

    def simulate_user_authentication(self):
        """Simulate user authentication scenarios."""
        self._log_with_count(
            "INFO",
            "Starting authentication simulation",
            {"simulation_type": "user_authentication"},
        )

        for user in self.users:
            # Simulate successful login
            if random.random() > 0.2:  # 80% success rate
                self._log_with_count(
                    "INFO",
                    f"User login successful",
                    {
                        **user.to_dict(),
                        "login_method": random.choice(["password", "oauth", "sso"]),
                        "ip_address": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                        "user_agent": random.choice(
                            [
                                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                                "Mozilla/5.0 (X11; Linux x86_64)",
                            ]
                        ),
                    },
                )

                # Log session creation
                session_id = str(uuid.uuid4())
                self._log_with_count(
                    "DEBUG",
                    "User session created",
                    {
                        "user_id": user.id,
                        "session_id": session_id,
                        "session_timeout": 3600,
                        "permissions": (
                            ["read", "write"] if user.role != "user" else ["read"]
                        ),
                    },
                )
            else:
                # Simulate failed login
                self._log_with_count(
                    "WARNING",
                    f"User login failed",
                    {
                        "user_id": user.id,
                        "email": user.email,
                        "failure_reason": random.choice(
                            ["invalid_password", "account_locked", "invalid_email"]
                        ),
                        "attempt_count": random.randint(1, 5),
                        "ip_address": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                    },
                )

    def simulate_transaction_processing(self):
        """Simulate financial transaction processing."""
        self._log_with_count(
            "INFO",
            "Starting transaction processing simulation",
            {"simulation_type": "transaction_processing"},
        )

        for i in range(15):  # Process 15 transactions
            user = random.choice(self.users)
            transaction = Transaction(
                id=f"txn_{i+1:03d}",
                user_id=user.id,
                amount=round(random.uniform(10.0, 1000.0), 2),
                currency=random.choice(["USD", "EUR", "GBP"]),
            )

            self._log_with_count(
                "INFO",
                "Transaction initiated",
                {
                    **transaction.to_dict(),
                    **user.to_dict(),
                    "processing_fee": round(transaction.amount * 0.025, 2),
                    "payment_method": random.choice(
                        ["credit_card", "bank_transfer", "digital_wallet"]
                    ),
                },
            )

            # Simulate processing steps
            self._log_with_count(
                "DEBUG",
                "Transaction validation started",
                {
                    "transaction_id": transaction.id,
                    "validation_checks": [
                        "amount_limit",
                        "account_balance",
                        "fraud_detection",
                    ],
                },
            )

            # Simulate different outcomes
            outcome = random.choices(
                ["success", "insufficient_funds",
                    "fraud_detected", "network_error"],
                weights=[0.7, 0.15, 0.1, 0.05],
            )[0]

            if outcome == "success":
                transaction.status = "completed"
                self._log_with_count(
                    "INFO",
                    "Transaction completed successfully",
                    {
                        **transaction.to_dict(),
                        "processing_time_ms": random.randint(100, 500),
                        "confirmation_code": f"CONF_{random.randint(100000, 999999)}",
                    },
                )
            elif outcome == "insufficient_funds":
                transaction.status = "failed"
                self._log_with_count(
                    "WARNING",
                    "Transaction failed - insufficient funds",
                    {
                        **transaction.to_dict(),
                        "available_balance": round(transaction.amount * 0.8, 2),
                        "required_amount": transaction.amount,
                    },
                )
            elif outcome == "fraud_detected":
                transaction.status = "blocked"
                self._log_with_count(
                    "ERROR",
                    "Transaction blocked - fraud detected",
                    {
                        **transaction.to_dict(),
                        "fraud_score": random.randint(80, 100),
                        "fraud_indicators": [
                            "unusual_location",
                            "high_amount",
                            "velocity_check",
                        ],
                    },
                )
            else:  # network_error
                transaction.status = "error"
                self._log_with_count(
                    "ERROR",
                    "Transaction failed - network error",
                    {
                        **transaction.to_dict(),
                        "error_code": "NET_001",
                        "retry_count": random.randint(1, 3),
                        "next_retry_in_seconds": 30,
                    },
                )

            self.transactions.append(transaction)

    def simulate_system_monitoring(self):
        """Simulate system monitoring and health checks."""
        self._log_with_count(
            "INFO",
            "Starting system monitoring simulation",
            {"simulation_type": "system_monitoring"},
        )

        # Database health checks
        for db in ["primary_db", "replica_db", "cache_db"]:
            response_time = random.uniform(5, 50)
            if response_time < 30:
                self._log_with_count(
                    "DEBUG",
                    f"Database health check passed",
                    {
                        "database": db,
                        "response_time_ms": round(response_time, 2),
                        "connection_pool_size": random.randint(5, 20),
                        "active_connections": random.randint(1, 15),
                    },
                )
            else:
                self._log_with_count(
                    "WARNING",
                    f"Database health check slow",
                    {
                        "database": db,
                        "response_time_ms": round(response_time, 2),
                        "threshold_ms": 30,
                        "recommendation": "investigate_performance",
                    },
                )

        # API endpoint monitoring
        endpoints = ["/api/users", "/api/transactions",
                     "/api/auth", "/api/reports"]
        for endpoint in endpoints:
            status_code = random.choices(
                [200, 404, 500, 503], weights=[0.8, 0.1, 0.05, 0.05]
            )[0]
            response_time = random.uniform(50, 300)

            if status_code == 200:
                self._log_with_count(
                    "DEBUG",
                    f"API endpoint healthy",
                    {
                        "endpoint": endpoint,
                        "status_code": status_code,
                        "response_time_ms": round(response_time, 2),
                        "requests_per_minute": random.randint(100, 1000),
                    },
                )
            else:
                level = "ERROR" if status_code >= 500 else "WARNING"
                self._log_with_count(
                    level,
                    f"API endpoint issue detected",
                    {
                        "endpoint": endpoint,
                        "status_code": status_code,
                        "response_time_ms": round(response_time, 2),
                        "error_rate_percent": random.uniform(1, 10),
                    },
                )

        # Resource utilization
        cpu_usage = random.uniform(20, 90)
        memory_usage = random.uniform(30, 85)
        disk_usage = random.uniform(40, 95)

        self._log_with_count(
            "INFO",
            "System resource utilization",
            {
                "cpu_usage_percent": round(cpu_usage, 2),
                "memory_usage_percent": round(memory_usage, 2),
                "disk_usage_percent": round(disk_usage, 2),
                "load_average": round(random.uniform(0.5, 4.0), 2),
                "network_io_mbps": round(random.uniform(10, 100), 2),
            },
        )

        # Alert if high usage
        if cpu_usage > 80:
            self._log_with_count(
                "WARNING",
                "High CPU usage detected",
                {
                    "cpu_usage_percent": round(cpu_usage, 2),
                    "threshold_percent": 80,
                    "top_processes": ["java", "python", "nginx"],
                },
            )

        if memory_usage > 80:
            self._log_with_count(
                "WARNING",
                "High memory usage detected",
                {
                    "memory_usage_percent": round(memory_usage, 2),
                    "threshold_percent": 80,
                    "available_memory_gb": round(random.uniform(1, 4), 2),
                },
            )

    def simulate_error_scenarios(self):
        """Simulate various error scenarios."""
        self._log_with_count(
            "INFO",
            "Starting error scenario simulation",
            {"simulation_type": "error_scenarios"},
        )

        # Simulate critical system errors
        critical_errors = [
            "Database connection pool exhausted",
            "Payment gateway unavailable",
            "Authentication service down",
            "File system full",
        ]

        for error in critical_errors[:2]:  # Only simulate 2 critical errors
            self._log_with_count(
                "CRITICAL",
                f"Critical system error: {error}",
                {
                    "error_type": "system_critical",
                    "impact": "service_degraded",
                    "estimated_recovery_time_minutes": random.randint(5, 30),
                    "affected_users": random.randint(100, 1000),
                    "incident_id": f"INC_{random.randint(100000, 999999)}",
                },
            )

        # Simulate application errors
        app_errors = [
            "Invalid JSON payload",
            "Rate limit exceeded",
            "Unauthorized access attempt",
            "Data validation failed",
        ]

        for error in app_errors:
            self._log_with_count(
                "ERROR",
                f"Application error: {error}",
                {
                    "error_type": "application",
                    "user_id": random.choice(self.users).id,
                    "request_id": str(uuid.uuid4()),
                    "stack_trace_available": True,
                    "auto_retry": error not in ["Unauthorized access attempt"],
                },
            )

    def generate_final_summary(self):
        """Generate final summary logs."""
        self._log_with_count(
            "INFO",
            "Generating comprehensive demo summary",
            {"simulation_type": "summary"},
        )

        # Transaction summary
        completed_transactions = [
            t for t in self.transactions if t.status == "completed"
        ]
        failed_transactions = [
            t for t in self.transactions if t.status in ["failed", "blocked", "error"]
        ]

        total_amount = sum(t.amount for t in completed_transactions)

        self._log_with_count(
            "INFO",
            "Transaction processing summary",
            {
                "total_transactions": len(self.transactions),
                "completed_transactions": len(completed_transactions),
                "failed_transactions": len(failed_transactions),
                "total_amount_processed": round(total_amount, 2),
                "average_transaction_amount": round(
                    (
                        total_amount / len(completed_transactions)
                        if completed_transactions
                        else 0
                    ),
                    2,
                ),
                "success_rate_percent": (
                    round(
                        (len(completed_transactions) /
                         len(self.transactions)) * 100, 2
                    )
                    if self.transactions
                    else 0
                ),
            },
        )

        # User activity summary
        self._log_with_count(
            "INFO",
            "User activity summary",
            {
                "total_users": len(self.users),
                "active_users": len([u for u in self.users if random.random() > 0.3]),
                "admin_users": len([u for u in self.users if u.role == "admin"]),
                "user_roles_distribution": {
                    "admin": len([u for u in self.users if u.role == "admin"]),
                    "moderator": len([u for u in self.users if u.role == "moderator"]),
                    "user": len([u for u in self.users if u.role == "user"]),
                },
            },
        )

        # Final system status
        self._log_with_count(
            "INFO",
            "Comprehensive demo completed successfully",
            {
                "total_log_entries_generated": self.log_count,
                "demo_duration_seconds": time.time() - self.start_time,
                "log_file_location": str(LOG_FILE),
                "demo_status": "completed",
                "all_simulations": [
                    "user_authentication",
                    "transaction_processing",
                    "system_monitoring",
                    "error_scenarios",
                ],
            },
        )

    def run_comprehensive_demo(self):
        """Run the complete comprehensive logging demonstration."""
        self.start_time = time.time()

        self._log_with_count(
            "INFO",
            "Starting comprehensive logging demonstration",
            {
                "target_log_count": TARGET_LOG_COUNT,
                "service": SERVICE_NAME,
                "version": SERVICE_VERSION,
            },
        )

        # Run all simulations
        self.simulate_user_authentication()
        self.simulate_transaction_processing()
        self.simulate_system_monitoring()
        self.simulate_error_scenarios()

        # Add some additional logs to reach target count
        while self.log_count < TARGET_LOG_COUNT - 5:
            self._log_with_count(
                "DEBUG",
                f"Additional debug log entry",
                {
                    "entry_number": self.log_count,
                    "random_data": {
                        "value": random.randint(1, 1000),
                        "timestamp": time.time(),
                        "uuid": str(uuid.uuid4()),
                    },
                },
            )

        self.generate_final_summary()

        return self.log_count


def main():
    """Main function to run the comprehensive demo."""
    print("🚀 Starting Comprehensive File Logging Demo")
    print(f"📁 Log file: {LOG_FILE}")
    print("⏳ Running simulation...")

    demo = ComprehensiveLoggingDemo()
    log_count = demo.run_comprehensive_demo()

    print(f"✅ Demo completed!")
    print(f"📊 Generated {log_count} log entries")
    print(f"📄 Check the log file: {LOG_FILE}")
    print(f"💡 All logs should be in the file, NOT in console!")

    # Verify log file exists and show stats
    if LOG_FILE.exists():
        file_size = LOG_FILE.stat().st_size
        with open(LOG_FILE, "r") as f:
            line_count = sum(1 for _ in f)

        print(f"📈 Log file stats:")
        print(f"   - Size: {file_size:,} bytes")
        print(f"   - Lines: {line_count:,}")
        print(
            f"   - Average bytes per line: {file_size // line_count if line_count > 0 else 0}"
        )
    else:
        print("❌ Log file was not created!")


if __name__ == "__main__":
    main()
