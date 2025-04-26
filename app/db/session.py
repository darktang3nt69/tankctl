"""Database session management."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Async engine for FastAPI
async_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
) if settings.DATABASE_URL.startswith('postgresql+asyncpg') else None

async_session = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
) if async_engine else None

# Sync engine for Celery and Flower
sync_engine = create_engine(
    settings.DATABASE_URL.replace('+asyncpg', '+psycopg2') if settings.DATABASE_URL.startswith('postgresql+asyncpg') else settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)
sync_session = sessionmaker(
    sync_engine,
    class_=Session,
    expire_on_commit=False
)

# Export engines
engine = async_engine or sync_engine  # For backward compatibility

# Async dependency for FastAPI
async def get_db():
    """Get database session."""
    if not async_session:
        raise RuntimeError("Async database session is not configured")
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# Sync dependency for Celery and Flower
def get_sync_db():
    """Get synchronous database session for Celery tasks."""
    session = sync_session()
    try:
        yield session
    finally:
        session.close()