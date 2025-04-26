"""Database initialization script."""

from sqlalchemy.orm import Session
from app.db.base_class import Base
from app.db.session import engine
from app.db.models import Tank, TankStatus, Command, Schedule, EventLog
from celery.backends.database.models import TaskSet, Task
from celery.backends.database.session import ResultModelBase

def init_db() -> None:
    """Initialize the database."""
    Base.metadata.create_all(bind=engine)
    ResultModelBase.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db() 