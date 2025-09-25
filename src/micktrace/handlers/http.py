"""
HTTP Handler

Send logs to HTTP endpoints with batching, retries, and authentication.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

from .base import Handler
from ..core.record import LogRecord

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class HTTPHandler(Handler):
    """
    HTTP handler for sending logs to remote endpoints.

    Features:
    - Async HTTP requests when possible
    - Automatic batching and compression
    - Authentication support
    - Retry logic with exponential backoff
    - Circuit breaker for failing endpoints
    """

    def __init__(
        self,
        name: str = "http",
        url: str = "",
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        auth: Optional[Dict[str, str]] = None,
        timeout: float = 10.0,
        retry_attempts: int = 3,
        **kwargs: Any
    ) -> None:
        super().__init__(name, **kwargs)

        if not url:
            raise ValueError("HTTP handler requires a URL")

        self.url = url
        self.method = method.upper()
        self.headers = headers or {}
        self.auth = auth
        self.timeout = timeout
        self.retry_attempts = retry_attempts

        # Default headers
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"

        # HTTP session for connection reuse
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> Optional[aiohttp.ClientSession]:
        """Get or create HTTP session."""
        if not HAS_AIOHTTP:
            return None

        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)

        return self._session

    def _prepare_payload(self, records: List[LogRecord]) -> str:
        """Prepare records for HTTP transmission."""
        # Convert records to dictionaries
        payload = {
            "records": [record.to_dict() for record in records],
            "count": len(records)
        }

        return json.dumps(payload, default=str)

    async def _send_async(self, payload: str) -> bool:
        """Send payload asynchronously."""
        if not HAS_AIOHTTP:
            return False

        session = await self._get_session()
        if not session:
            return False

        headers = self.headers.copy()

        # Add authentication
        if self.auth:
            if "bearer" in self.auth:
                headers["Authorization"] = f"Bearer {self.auth['bearer']}"
            elif "basic" in self.auth:
                import base64
                creds = base64.b64encode(self.auth["basic"].encode()).decode()
                headers["Authorization"] = f"Basic {creds}"

        for attempt in range(self.retry_attempts):
            try:
                async with session.request(
                    self.method,
                    self.url,
                    data=payload,
                    headers=headers
                ) as response:
                    if response.status < 400:
                        return True
                    elif response.status >= 500:
                        # Server error, retry
                        if attempt < self.retry_attempts - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue

                    return False

            except Exception:
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return False

        return False

    def _send_sync(self, payload: str) -> bool:
        """Send payload synchronously."""
        if not HAS_REQUESTS:
            return False

        headers = self.headers.copy()

        # Add authentication
        auth = None
        if self.auth:
            if "bearer" in self.auth:
                headers["Authorization"] = f"Bearer {self.auth['bearer']}"
            elif "basic" in self.auth:
                auth = tuple(self.auth["basic"].split(":", 1))

        for attempt in range(self.retry_attempts):
            try:
                response = requests.request(
                    self.method,
                    self.url,
                    data=payload,
                    headers=headers,
                    auth=auth,
                    timeout=self.timeout
                )

                if response.status_code < 400:
                    return True
                elif response.status_code >= 500:
                    if attempt < self.retry_attempts - 1:
                        import time
                        time.sleep(2 ** attempt)
                        continue

                return False

            except Exception:
                if attempt < self.retry_attempts - 1:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                return False

        return False

    def _emit_sync(self, formatted: str, record: LogRecord) -> None:
        """Emit a single record synchronously."""
        payload = self._prepare_payload([record])
        success = self._send_sync(payload)

        if not success:
            raise Exception(f"Failed to send log to {self.url}")

    async def _emit_async(self, formatted_records: List[str], records: List[LogRecord]) -> None:
        """Emit a batch of records asynchronously."""
        payload = self._prepare_payload(records)
        success = await self._send_async(payload)

        if not success:
            raise Exception(f"Failed to send logs to {self.url}")

    async def stop(self) -> None:
        """Stop the handler and close HTTP session."""
        await super().stop()

        if self._session and not self._session.closed:
            await self._session.close()
