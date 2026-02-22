"""
ThinkAloud.ai — Database Configuration
Async SQLAlchemy engine, session factory, and Base class.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Only log SQL in debug mode
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
