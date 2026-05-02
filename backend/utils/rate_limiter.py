"""
Sliding window rate limiter middleware for FastAPI.
Limits requests per IP address to prevent abuse.
"""

import time
from collections import defaultdict
from typing import Dict, List

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter.
    Tracks request timestamps per client IP and rejects
    requests that exceed the configured limit.
    """

    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _cleanup_old_requests(self, ip: str, now: float) -> None:
        """Remove request timestamps outside the sliding window."""
        cutoff = now - self.window_seconds
        self._requests[ip] = [
            ts for ts in self._requests[ip] if ts > cutoff
        ]

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = time.time()

        self._cleanup_old_requests(client_ip, now)

        if len(self._requests[client_ip]) >= self.requests_per_minute:
            # Calculate retry-after
            oldest = self._requests[client_ip][0]
            retry_after = int(self.window_seconds - (now - oldest)) + 1

            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": retry_after,
                    "limit": self.requests_per_minute,
                },
                headers={"Retry-After": str(retry_after)},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)
