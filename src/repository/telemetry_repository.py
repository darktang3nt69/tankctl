"""
Repository layer for telemetry data.

Handles database access for telemetry stored in TimescaleDB.
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text, desc
from sqlalchemy.orm import Session

from src.domain.command import Command, CommandStatus
from src.infrastructure.db.models import CommandModel
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CommandRepository:
    """Repository for command operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create(self, command: Command) -> Command:
        """
        Create a new command.

        Args:
            command: Command domain model

        Returns:
            Created command

        Raises:
            Exception: If creation fails
        """
        try:
            db_command = CommandModel(
                device_id=command.device_id,
                command=command.command,
                value=command.value,
                version=command.version,
                status=command.status,
                created_at=command.created_at,
                sent_at=command.sent_at,
                executed_at=command.executed_at,
            )
            self.session.add(db_command)
            self.session.commit()
            command.id = db_command.id
            logger.debug(
                "command_created",
                device_id=command.device_id,
                command=command.command,
            )
            return command
        except Exception as e:
            self.session.rollback()
            logger.error("command_creation_failed", error=str(e))
            raise

    def get_by_id(self, command_id: int) -> Optional[Command]:
        """
        Get command by ID.

        Args:
            command_id: Command ID

        Returns:
            Command or None if not found
        """
        try:
            db_command = self.session.query(CommandModel).filter(
                CommandModel.id == command_id
            ).first()

            if not db_command:
                return None

            return self._model_to_domain(db_command)
        except Exception as e:
            logger.error("command_get_failed", command_id=command_id, error=str(e))
            raise

    def get_pending_for_device(self, device_id: str) -> list[Command]:
        """
        Get all pending commands for a device.

        Args:
            device_id: Device ID

        Returns:
            List of pending commands
        """
        try:
            db_commands = self.session.query(CommandModel).filter(
                CommandModel.device_id == device_id,
                CommandModel.status == CommandStatus.PENDING,
            ).all()

            return [self._model_to_domain(cmd) for cmd in db_commands]
        except Exception as e:
            logger.error("commands_get_pending_failed", device_id=device_id, error=str(e))
            raise

    def get_latest_for_device(self, device_id: str, limit: int = 10) -> list[Command]:
        """
        Get latest commands for a device.

        Args:
            device_id: Device ID
            limit: Maximum number of commands to return

        Returns:
            List of commands ordered by creation date
        """
        try:
            db_commands = (
                self.session.query(CommandModel)
                .filter(CommandModel.device_id == device_id)
                .order_by(desc(CommandModel.created_at))
                .limit(limit)
                .all()
            )

            return [self._model_to_domain(cmd) for cmd in db_commands]
        except Exception as e:
            logger.error("commands_get_latest_failed", device_id=device_id, error=str(e))
            raise

    def update_status(self, command_id: int, status: str) -> Optional[Command]:
        """
        Update command status.

        Args:
            command_id: Command ID
            status: New status

        Returns:
            Updated command or None if not found
        """
        try:
            db_command = self.session.query(CommandModel).filter(
                CommandModel.id == command_id
            ).first()

            if not db_command:
                return None

            db_command.status = status

            if status == CommandStatus.SENT:
                db_command.sent_at = datetime.utcnow()
            elif status == CommandStatus.EXECUTED:
                db_command.executed_at = datetime.utcnow()

            self.session.commit()
            logger.debug(
                "command_status_updated",
                command_id=command_id,
                status=status,
            )
            return self._model_to_domain(db_command)
        except Exception as e:
            self.session.rollback()
            logger.error("command_status_update_failed", command_id=command_id, error=str(e))
            raise

    def _model_to_domain(self, db_command: CommandModel) -> Command:
        """Convert database model to domain model."""
        return Command(
            id=db_command.id,
            device_id=db_command.device_id,
            command=db_command.command,
            value=db_command.value,
            version=db_command.version,
            status=db_command.status,
            created_at=db_command.created_at,
            sent_at=db_command.sent_at,
            executed_at=db_command.executed_at,
        )


class TelemetryRepository:
    """Repository for telemetry operations in TimescaleDB."""

    def __init__(self, session: Session):
        """Initialize repository with TimescaleDB session."""
        self.session = session

    def insert(
        self,
        device_id: str,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        pressure: Optional[float] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Insert telemetry data point into TimescaleDB.

        Args:
            device_id: Device identifier
            temperature: Temperature reading (optional)
            humidity: Humidity reading (optional)
            pressure: Pressure reading (optional)
            metadata: Additional metadata as dict (optional)

        Raises:
            Exception: If insertion fails
        """
        try:
            # Use raw SQL for direct TimescaleDB insertion
            query = text("""
                INSERT INTO telemetry (time, device_id, temperature, humidity, pressure, metadata)
                VALUES (NOW() AT TIME ZONE 'UTC', :device_id, :temperature, :humidity, :pressure, :metadata)
            """)
            
            self.session.execute(
                query,
                {
                    "device_id": device_id,
                    "temperature": temperature,
                    "humidity": humidity,
                    "pressure": pressure,
                    "metadata": metadata,
                },
            )
            self.session.commit()
            
            logger.debug(
                "telemetry_inserted",
                device_id=device_id,
                temperature=temperature,
                humidity=humidity,
                pressure=pressure,
            )
        except Exception as e:
            self.session.rollback()
            logger.error("telemetry_insertion_failed", device_id=device_id, error=str(e))
            raise

    def get_recent(
        self,
        device_id: str,
        limit: int = 100,
        hours: Optional[int] = None,
    ) -> list[dict]:
        """
        Get recent telemetry for a device.

        Args:
            device_id: Device identifier
            limit: Maximum number of records (default 100)
            hours: Optional time window in hours (default: all time)

        Returns:
            List of telemetry records with time, temperature, humidity, pressure
        """
        try:
            where_clause = "WHERE device_id = :device_id"
            params = {"device_id": device_id, "limit": limit}
            
            if hours:
                where_clause += " AND time > NOW() - (:hours * INTERVAL '1 hour')"
                params["hours"] = hours
            
            query = text(f"""
                SELECT
                    time,
                    device_id,
                    temperature,
                    humidity,
                    pressure,
                    metadata
                FROM telemetry
                {where_clause}
                ORDER BY time DESC
                LIMIT :limit
            """)
            
            results = self.session.execute(query, params).fetchall()
            
            # Convert to list of dicts
            telemetry_list = []
            for row in results:
                telemetry_list.append({
                    "time": row[0].isoformat() if row[0] else None,
                    "device_id": row[1],
                    "temperature": row[2],
                    "humidity": row[3],
                    "pressure": row[4],
                    "metadata": row[5],
                })
            
            logger.debug(
                "telemetry_retrieved",
                device_id=device_id,
                count=len(telemetry_list),
            )
            
            return telemetry_list
        except Exception as e:
            logger.error("telemetry_retrieval_failed", device_id=device_id, error=str(e))
            raise

    def get_by_metric(
        self,
        device_id: str,
        metric: str,
        limit: int = 100,
    ) -> list[dict]:
        """
        Get specific metric for device.

        Args:
            device_id: Device identifier
            metric: Metric name ('temperature', 'humidity', or 'pressure')
            limit: Maximum number of records

        Returns:
            List of records with time and metric value
        """
        if metric not in ("temperature", "humidity", "pressure"):
            raise ValueError(f"Invalid metric: {metric}")
        
        try:
            query = text(f"""
                SELECT
                    time,
                    device_id,
                    {metric}
                FROM telemetry
                WHERE device_id = :device_id AND {metric} IS NOT NULL
                ORDER BY time DESC
                LIMIT :limit
            """)
            
            results = self.session.execute(
                query,
                {"device_id": device_id, "limit": limit},
            ).fetchall()
            
            # Convert to list of dicts
            metric_list = []
            for row in results:
                metric_list.append({
                    "time": row[0].isoformat() if row[0] else None,
                    "device_id": row[1],
                    "value": row[2],
                })
            
            logger.debug(
                "metric_retrieved",
                device_id=device_id,
                metric=metric,
                count=len(metric_list),
            )
            
            return metric_list
        except Exception as e:
            logger.error(
                "metric_retrieval_failed",
                device_id=device_id,
                metric=metric,
                error=str(e),
            )
            raise

    def get_hourly_rollup(
        self,
        device_id: str,
        hours: int = 24,
    ) -> list[dict]:
        """
        Get hourly aggregated telemetry for device.

        Uses the pre-aggregated continuous aggregate view for efficiency.

        Args:
            device_id: Device identifier
            hours: Number of hours to retrieve (default 24)

        Returns:
            List of hourly aggregated records
        """
        try:
            query = text("""
                SELECT
                    hour,
                    device_id,
                    temp_avg,
                    temp_max,
                    temp_min,
                    humidity_avg,
                    humidity_max,
                    humidity_min,
                    sample_count
                FROM telemetry_hourly
                WHERE device_id = :device_id AND hour > NOW() - (:hours * INTERVAL '1 hour')
                ORDER BY hour DESC
            """)
            
            results = self.session.execute(
                query,
                {"device_id": device_id, "hours": hours},
            ).fetchall()
            
            # Convert to list of dicts
            rollup_list = []
            for row in results:
                rollup_list.append({
                    "hour": row[0].isoformat() if row[0] else None,
                    "device_id": row[1],
                    "temperature": {
                        "avg": row[2],
                        "max": row[3],
                        "min": row[4],
                    },
                    "humidity": {
                        "avg": row[5],
                        "max": row[6],
                        "min": row[7],
                    },
                    "sample_count": row[8],
                })
            
            logger.debug(
                "hourly_rollup_retrieved",
                device_id=device_id,
                count=len(rollup_list),
            )
            
            return rollup_list
        except Exception as e:
            logger.error(
                "hourly_rollup_failed",
                device_id=device_id,
                error=str(e),
            )
            raise

