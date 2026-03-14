"""
Database initialization and session management for TankCtl.
"""

from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, scoped_session

from src.config.settings import settings
from src.infrastructure.db.models import (
    Base,
    DeviceModel,
    DeviceShadowModel,
    CommandModel,
    EventRecord,
    LightScheduleModel,
    WarningAcknowledgementModel,
    DevicePushTokenModel,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Database:
    """Database connection and session manager."""

    def __init__(self):
        """Initialize database engine."""
        self.engine = create_engine(
            settings.database.url,
            echo=settings.api.debug,
            pool_pre_ping=True,  # Verify connections before using
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

        # Setup TimescaleDB connection if different
        if settings.timescale.url != settings.database.url:
            self.timescale_engine = create_engine(
                settings.timescale.url,
                echo=settings.api.debug,
                pool_pre_ping=True,
            )
            self.TimescaleSessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.timescale_engine,
            )
        else:
            self.timescale_engine = self.engine
            self.TimescaleSessionLocal = self.SessionLocal

    def init_db(self) -> None:
        """Initialize database tables."""
        logger.info("db_initializing")
        try:
            Base.metadata.create_all(
                bind=self.engine,
                tables=[
                    DeviceModel.__table__,
                    DeviceShadowModel.__table__,
                    CommandModel.__table__,
                    EventRecord.__table__,
                    LightScheduleModel.__table__,
                    WarningAcknowledgementModel.__table__,
                    DevicePushTokenModel.__table__,
                ],
            )
            self._init_timescale_schema()
            logger.info("db_initialized_successfully")
        except Exception as e:
            logger.error("db_initialization_failed", error=str(e))
            raise

    def _init_timescale_schema(self) -> None:
        """Initialize TimescaleDB telemetry schema from migration SQL."""
        logger.info("timescale_schema_initializing")

        migration_file = (
            Path(__file__).resolve().parents[3]
            / "migrations"
            / "001_create_telemetry_table.sql"
        )

        if not migration_file.exists():
            logger.warning(
                "timescale_migration_missing",
                migration_file=str(migration_file),
            )
            return

        try:
            with self.timescale_engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
                conn.commit()

                sql_script = migration_file.read_text(encoding="utf-8")
                statements = [stmt.strip() for stmt in sql_script.split(";") if stmt.strip()]

                for statement in statements:
                    lower_stmt = statement.lower()

                    if "telemetry_hourly" in lower_stmt or "continuous_aggregate" in lower_stmt:
                        logger.warning(
                            "timescale_statement_skipped",
                            reason="continuous_aggregate_not_required_for_startup",
                            statement=statement[:120],
                        )
                        continue

                    trans = conn.begin()
                    try:
                        conn.exec_driver_sql(statement)
                        trans.commit()
                    except Exception as statement_error:
                        trans.rollback()

                        is_optional_statement = any(
                            keyword in lower_stmt
                            for keyword in (
                                "add_retention_policy",
                                "add_continuous_aggregate_policy",
                                "create_hypertable",
                                "create index if not exists",
                            )
                        )

                        if is_optional_statement:
                            logger.warning(
                                "timescale_optional_statement_failed",
                                statement=statement[:120],
                                error=str(statement_error),
                            )
                            continue

                        raise

            logger.info("timescale_schema_ready")
        except Exception as e:
            logger.error("timescale_schema_init_failed", error=str(e))
            raise

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def get_timescale_session(self) -> Session:
        """Get a new TimescaleDB session for telemetry."""
        return self.TimescaleSessionLocal()

    def close(self) -> None:
        """Close database connections."""
        self.engine.dispose()
        if self.timescale_engine != self.engine:
            self.timescale_engine.dispose()
        logger.info("db_closed")


# Singleton database instance
db = Database()

# Define a function to provide a database session dependency
def get_db():
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()
