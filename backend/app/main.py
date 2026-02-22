"""
ThinkAloud.ai — FastAPI Application Entry Point
"""
import logging
import sys
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.db import engine
from app.db.redis import get_redis, close_redis

# Import routers
from app.api.v1.auth import router as auth_router
from app.api.v1.problems import router as problems_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.stats import router as stats_router
from app.api.v1.users import router as users_router
from app.api.v1.voice import router as voice_router
from app.api.v1.ai import router as ai_router

# Import middleware & error handlers
from app.core.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from app.core.exceptions import register_exception_handlers

from app.core.logging_config import setup_logging
from app.core.metrics import RequestMetricsMiddleware
setup_logging(debug=settings.debug)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: logger.info("✅ Database connected"))
    redis = await get_redis()
    await redis.ping()
    logger.info("✅ Redis connected")

    yield

    await close_redis()
    logger.info("🔌 Redis disconnected")


app = FastAPI(
    title="ThinkAloud.ai",
    description="AI-powered interview practice platform",
    version="2.0.0",
    lifespan=lifespan,
)

# Global error handlers
register_exception_handlers(app)

# Security middleware (first added = outermost)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestMetricsMiddleware)


# CORS — origins loaded from environment
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
app.include_router(problems_router, prefix="/api/v1/problems", tags=["problems"])
app.include_router(sessions_router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(stats_router, prefix="/api/v1/stats", tags=["stats"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(voice_router, prefix="/api/v1/voice", tags=["voice"])
app.include_router(ai_router, prefix="/api/v1/ai", tags=["ai"])
# Serve uploaded files (avatars, etc.)
os.makedirs("uploads/avatars", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")



@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
