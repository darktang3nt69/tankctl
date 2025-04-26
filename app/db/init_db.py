"""Database initialization script."""

import asyncio
from sqlalchemy.ext.asyncio import AsyncEngine
from app.db.base_class import Base
from app.db.session import engine
from app.db.models import Tank, TankStatus, Command, Schedule, EventLog
from celery.backends.database.models import TaskSet, Task
from celery.backends.database.session import ResultModelBase

async def init_db_async() -> None:
    """Initialize the database asynchronously."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(ResultModelBase.metadata.create_all)

def init_db() -> None:
    """Initialize the database."""
    asyncio.run(init_db_async())

if __name__ == "__main__":
    init_db() 