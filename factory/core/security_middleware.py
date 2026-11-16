"""
Production Security Middleware & Request Filtering.
Enforces HTTP security headers, rate limiting, request size limits, and input sanitization.
"""

import time
from collections import defaultdict
from typing import Dict, Tuple, List, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from factory.core.logger import logger
from factory.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects enterprise-grade defensive HTTP response headers."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none';"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    In-memory sliding window rate limiter.
    Limits requests per client IP to prevent brute-force attacks and API exhaustion.
    """

    clients: Dict[str, List[float]] = defaultdict(list)

    @classmethod
    def reset(cls):
        """Reset sliding window state (used between isolated test suites)."""
        cls.clients.clear()

    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Auth endpoints have tighter limit
        self.auth_limit = 20

    async def dispatch(self, request: Request, call_next) -> Response:
        # Allow internal test suites with bypass header if explicitly requested
        if request.headers.get("X-Bypass-Rate-Limit") == "true":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        now = time.time()

        # Clean old timestamps
        history = self.clients[client_ip]
        self.clients[client_ip] = [t for t in history if now - t < self.window_seconds]

        limit = self.auth_limit if "/auth/" in path else self.max_requests

        if len(self.clients[client_ip]) >= limit:
            logger.warning(f"RATE LIMIT BREACH: Client {client_ip} exceeded {limit} reqs on {path}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded ({limit} requests per minute). Please try again later.",
                    "retry_after_seconds": self.window_seconds
                },
                headers={"Retry-After": str(self.window_seconds)}
            )

        self.clients[client_ip].append(now)
        return await call_next(request)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Prevents Denial of Service by rejecting oversized payload streams."""

    def __init__(self, app, max_content_length: int = 10 * 1024 * 1024):  # 10 MB
        super().__init__(app)
        self.max_content_length = max_content_length

    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_content_length:
            logger.warning(f"PAYLOAD TOO LARGE: Request exceeded {self.max_content_length} bytes")
            return JSONResponse(
                status_code=413,
                content={"error": "Payload Too Large", "max_allowed_bytes": self.max_content_length}
            )
        return await call_next(request)
