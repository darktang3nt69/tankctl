from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# ------------------------------------------------------------
# Database URL Format:
# postgresql://<username>:<password>@<server>:<port>/<database_name>
# ------------------------------------------------------------
DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

# Create SQLAlchemy Engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.SQLALCHEMY_POOL_SIZE,
    max_overflow=settings.SQLALCHEMY_MAX_OVERFLOW,
    pool_recycle=settings.SQLALCHEMY_POOL_RECYCLE,
    pool_timeout=settings.SQLALCHEMY_POOL_TIMEOUT,
)

# Create a configured "SessionLocal" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for our ORM models
Base = declarative_base()

# Dependency - to be used inside API routes
def get_db():
    """
    Provides a database session to routes, automatically closing it after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
