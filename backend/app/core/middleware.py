"""
ThinkAloud.ai — Middleware
Rate limiting and security headers.
"""
import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.db.redis import get_redis

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple Redis-based rate limiter.
    Limits per IP: 100 requests/minute for general, 10/minute for auth.
    """

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        path = request.url.path

        # Choose rate limit based on path
        if "/api/v1/signup" in path or "/api/v1/login" in path or "/api/v1/forgot" in path:
            limit, window, prefix = 10, 60, "rl:auth"
        elif "/api/v1/" in path:
            limit, window, prefix = 100, 60, "rl:api"
        else:
            return await call_next(request)

        key = f"{prefix}:{client_ip}"

        try:
            redis = await get_redis()
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, window)

            if current > limit:
                logger.warning(f"Rate limit exceeded: {client_ip} on {path}")
                return Response(
                    content='{"detail":"Too many requests. Slow down."}',
                    status_code=429,
                    media_type="application/json",
                )
        except Exception:
            # If Redis is down, allow the request through
            pass

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        return response
