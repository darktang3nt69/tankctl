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
)
async_session = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Sync engine for Celery
sync_engine = create_engine(
    settings.DATABASE_URL.replace('+asyncpg', '+psycopg2'),
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
engine = async_engine  # For backward compatibility

# Async dependency for FastAPI
async def get_db():
    """Get database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# Sync dependency for Celery
def get_sync_db():
    """Get synchronous database session for Celery tasks."""
    session = sync_session()
    try:
        yield session
    finally:
        session.close()