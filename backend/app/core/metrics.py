"""
ThinkAloud.ai — Request Metrics Middleware
Logs every request with latency, status code, and path.
"""
import time
import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.metrics")


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """Log request metrics: method, path, status, latency."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()

        response = await call_next(request)

        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "client_ip": request.client.host,
            },
        )

        return response
