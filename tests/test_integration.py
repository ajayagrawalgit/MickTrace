"""
Integration tests for MickTrace.
Tests real-world usage scenarios and end-to-end functionality.
"""

import asyncio
import tempfile
import os
import pytest
import micktrace


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def setup_method(self):
        """Setup for each test."""
        micktrace.clear_context()

    def test_web_application_scenario(self):
        """Test typical web application logging scenario."""
        # Configure logging like a web application would
        micktrace.configure(
            level="INFO",
            format="structured",
            service="web-app",
            version="1.0.0",
            environment="test",
            handlers=[{"type": "memory"}],
        )

        # Simulate web request processing
        logger = micktrace.get_logger("web_app")

        with micktrace.context(request_id="req_123", user_id=456):
            logger.info("Request started", method="POST", path="/api/users")

            # Simulate service calls
            auth_logger = logger.bind(component="auth")
            auth_logger.info("Authenticating user")
            auth_logger.info("User authenticated successfully")

            # Simulate database operations
            db_logger = logger.bind(component="database")
            db_logger.info("Executing query", table="users", operation="INSERT")
            db_logger.info("Query completed", rows_affected=1)

            # Simulate response
            logger.info("Request completed", status_code=201, duration_ms=150)

    def test_microservices_scenario(self):
        """Test microservices distributed tracing scenario."""
        micktrace.configure(level="INFO", handlers=[{"type": "memory"}])

        # Simulate distributed trace across services
        trace_id = "trace_abc123"

        # Service 1: API Gateway
        gateway_logger = micktrace.get_logger("api_gateway")
        with micktrace.context(trace_id=trace_id, span_id="span_001"):
            gateway_logger.info("Request received", service="api_gateway")

            # Service 2: User Service
            user_logger = micktrace.get_logger("user_service")
            with micktrace.context(span_id="span_002", parent_span="span_001"):
                user_logger.info("Validating user", service="user_service")
                user_logger.info("User validation completed")

            # Service 3: Order Service
            order_logger = micktrace.get_logger("order_service")
            with micktrace.context(span_id="span_003", parent_span="span_001"):
                order_logger.info("Processing order", service="order_service")
                order_logger.info("Order processed successfully")

            gateway_logger.info("Request completed")

    @pytest.mark.asyncio
    async def test_async_application_scenario(self):
        """Test async application scenario."""
        micktrace.configure(level="INFO", handlers=[{"type": "memory"}])

        async def process_user_request(user_id: int):
            """Simulate async user request processing."""
            async with micktrace.acontext(user_id=user_id):
                logger = micktrace.get_logger("async_app")
                logger.info("Processing user request")

                # Simulate async operations
                await asyncio.sleep(0.01)
                logger.info("Database query completed")

                await asyncio.sleep(0.01)
                logger.info("External API call completed")

                logger.info("User request processed successfully")
                return f"processed_user_{user_id}"

        # Process multiple users concurrently
        tasks = [process_user_request(i) for i in range(1, 6)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(result.startswith("processed_user_") for result in results)

    def test_error_handling_scenario(self):
        """Test comprehensive error handling scenario."""
        micktrace.configure(level="DEBUG", handlers=[{"type": "memory"}])

        logger = micktrace.get_logger("error_handling_test")

        with micktrace.context(operation="test_operation", user_id=123):
            try:
                logger.info("Starting risky operation")

                # Simulate different types of errors
                try:
                    raise ValueError("Invalid input data")
                except ValueError as e:
                    logger.warning(
                        "Input validation failed",
                        error_type=type(e).__name__,
                        error_message=str(e),
                        recoverable=True,
                    )

                # Simulate recovery and retry
                logger.info("Retrying operation with corrected data")

                try:
                    raise ConnectionError("Database connection failed")
                except ConnectionError as e:
                    logger.error(
                        "Database connection failed",
                        error_type=type(e).__name__,
                        error_message=str(e),
                        retry_count=1,
                    )

                    # Simulate successful retry
                    logger.info("Retry successful")

                logger.info("Operation completed successfully")

            except Exception as e:
                logger.exception(
                    "Unexpected error in operation",
                    operation="test_operation",
                    error_type=type(e).__name__,
                )

    def test_batch_processing_scenario(self):
        """Test batch processing scenario."""
        micktrace.configure(level="INFO", handlers=[{"type": "memory"}])

        logger = micktrace.get_logger("batch_processor")

        batch_id = "batch_001"
        items = [{"id": i, "data": f"item_{i}"} for i in range(1, 11)]

        with micktrace.context(batch_id=batch_id):
            logger.info(
                "Batch processing started", batch_id=batch_id, item_count=len(items)
            )

            processed_count = 0
            failed_count = 0

            for item in items:
                item_logger = logger.bind(item_id=item["id"])

                try:
                    item_logger.debug("Processing item", item_data=item["data"])

                    # Simulate processing (some items fail)
                    if item["id"] % 7 == 0:  # Simulate failure
                        raise RuntimeError(f"Processing failed for item {item['id']}")

                    item_logger.info("Item processed successfully")
                    processed_count += 1

                except Exception as e:
                    item_logger.error(
                        "Item processing failed",
                        error_type=type(e).__name__,
                        error_message=str(e),
                    )
                    failed_count += 1

            logger.info(
                "Batch processing completed",
                total_items=len(items),
                processed_count=processed_count,
                failed_count=failed_count,
                success_rate=processed_count / len(items),
            )

    def test_multi_handler_scenario(self):
        """Test scenario with multiple handlers."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Configure multiple handlers
            micktrace.configure(
                level="DEBUG",
                handlers=[
                    {"type": "console", "level": "INFO"},
                    {"type": "file", "level": "DEBUG", "config": {"path": tmp_path}},
                    {"type": "memory", "level": "WARNING"},
                ],
            )

            logger = micktrace.get_logger("multi_handler_test")

            # Log at different levels
            logger.debug("Debug message (file only)")
            logger.info("Info message (console + file)")
            logger.warning("Warning message (all handlers)")
            logger.error("Error message (all handlers)")

            # Verify file handler worked
            assert os.path.exists(tmp_path)
            with open(tmp_path, "r") as f:
                content = f.read()
                assert "Debug message" in content
                assert "Info message" in content
                assert "Warning message" in content
                assert "Error message" in content

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestLibraryIntegration:
    """Test integration patterns for library developers."""

    def test_library_logging_pattern(self):
        """Test typical library logging pattern."""

        # Simulate library code that uses micktrace
        class MyLibrary:
            def __init__(self):
                self.logger = micktrace.get_logger("my_library")

            def process_data(self, data):
                self.logger.debug("Processing data", data_size=len(data))

                # Simulate processing
                result = data.upper()

                self.logger.info(
                    "Data processed successfully",
                    input_size=len(data),
                    output_size=len(result),
                )
                return result

            def handle_error(self, error_data):
                try:
                    # Simulate error condition
                    if "error" in error_data:
                        raise ValueError("Invalid data")
                    return "success"
                except Exception as e:
                    self.logger.exception(
                        "Error in library function",
                        error_data=error_data,
                        error_type=type(e).__name__,
                    )
                    raise

        # Application configures logging
        micktrace.configure(level="INFO", handlers=[{"type": "memory"}])

        # Library should work without knowing about configuration
        lib = MyLibrary()
        result = lib.process_data("test data")
        assert result == "TEST DATA"

        # Test error handling
        with pytest.raises(ValueError):
            lib.handle_error("error data")

    def test_library_with_bound_context(self):
        """Test library using bound loggers for context."""

        class DatabaseLibrary:
            def __init__(self, db_name: str):
                self.logger = micktrace.get_logger("db_lib").bind(
                    component="database", db_name=db_name
                )

            def connect(self):
                self.logger.info("Connecting to database")
                return "connected"

            def query(self, sql: str):
                query_logger = self.logger.bind(operation="query")
                query_logger.debug("Executing query", sql=sql)
                query_logger.info("Query executed successfully", rows_returned=5)
                return ["row1", "row2", "row3", "row4", "row5"]

        micktrace.configure(level="DEBUG", handlers=[{"type": "memory"}])

        db = DatabaseLibrary("test_db")
        db.connect()
        results = db.query("SELECT * FROM users")
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_async_library_integration(self):
        """Test async library integration."""

        class AsyncHttpClient:
            def __init__(self):
                self.logger = micktrace.get_logger("http_client")

            async def get(self, url: str):
                async with micktrace.acontext(url=url, method="GET"):
                    self.logger.info("HTTP request started")

                    # Simulate async HTTP request
                    await asyncio.sleep(0.01)

                    self.logger.info(
                        "HTTP request completed", status_code=200, response_size=1024
                    )
                    return {"status": 200, "data": "response"}

            async def post(self, url: str, data: dict):
                async with micktrace.acontext(url=url, method="POST"):
                    self.logger.info(
                        "HTTP POST request started", data_size=len(str(data))
                    )

                    await asyncio.sleep(0.02)

                    self.logger.info("HTTP POST request completed", status_code=201)
                    return {"status": 201, "id": "created"}

        micktrace.configure(level="INFO", handlers=[{"type": "memory"}])

        client = AsyncHttpClient()

        # Test concurrent requests
        tasks = [
            client.get("https://api.example.com/users"),
            client.post("https://api.example.com/users", {"name": "test"}),
            client.get("https://api.example.com/orders"),
        ]

        results = await asyncio.gather(*tasks)
        assert len(results) == 3
        assert all("status" in result for result in results)


class TestEndToEndScenarios:
    """Test complete end-to-end scenarios."""

    def test_complete_application_flow(self):
        """Test complete application flow from start to finish."""
        # Application startup
        micktrace.configure(
            level="INFO",
            service="test_app",
            version="1.0.0",
            environment="test",
            handlers=[{"type": "memory"}],
        )

        app_logger = micktrace.get_logger("app")
        app_logger.info("Application starting up")

        # Simulate request processing
        request_id = "req_001"
        user_id = 12345

        with micktrace.context(request_id=request_id, user_id=user_id):
            # Request received
            api_logger = micktrace.get_logger("api")
            api_logger.info(
                "Request received",
                method="POST",
                path="/api/users",
                content_type="application/json",
            )

            # Authentication
            auth_logger = api_logger.bind(component="auth")
            auth_logger.info("Authenticating user")
            auth_logger.info("User authenticated successfully", auth_method="jwt")

            # Business logic
            business_logger = api_logger.bind(component="business_logic")
            business_logger.info("Processing business logic")

            # Database operations
            db_logger = business_logger.bind(component="database")
            db_logger.info("Starting database transaction")
            db_logger.info("Inserting user record", table="users")
            db_logger.info("Database transaction committed")

            # External API call
            external_logger = business_logger.bind(component="external_api")
            external_logger.info(
                "Calling external service", service="notification_service"
            )
            external_logger.info(
                "External service call completed", response_time_ms=250
            )

            # Response
            api_logger.info(
                "Request completed successfully", status_code=201, total_duration_ms=500
            )

        # Application continues running
        app_logger.info("Request processing completed")

    @pytest.mark.asyncio
    async def test_complete_async_application_flow(self):
        """Test complete async application flow."""
        micktrace.configure(level="INFO", handlers=[{"type": "memory"}])

        app_logger = micktrace.get_logger("async_app")

        async def handle_user_signup(user_data: dict):
            """Complete user signup flow."""
            async with micktrace.acorrelation(
                operation="user_signup"
            ) as correlation_id:
                signup_logger = app_logger.bind(
                    operation="signup", correlation_id=correlation_id
                )

                signup_logger.info("User signup started", email=user_data["email"])

                # Validate user data
                await asyncio.sleep(0.01)
                signup_logger.info("User data validated")

                # Check if user exists
                await asyncio.sleep(0.02)
                signup_logger.info("User existence check completed")

                # Create user account
                await asyncio.sleep(0.03)
                signup_logger.info("User account created", user_id=user_data["id"])

                # Send welcome email
                await asyncio.sleep(0.02)
                signup_logger.info("Welcome email sent")

                signup_logger.info(
                    "User signup completed successfully", total_duration_ms=80
                )

                return {"user_id": user_data["id"], "status": "created"}

        # Process multiple signups concurrently
        users = [
            {"id": 1, "email": "user1@example.com"},
            {"id": 2, "email": "user2@example.com"},
            {"id": 3, "email": "user3@example.com"},
        ]

        tasks = [handle_user_signup(user) for user in users]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all(result["status"] == "created" for result in results)
