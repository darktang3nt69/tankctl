"""
Telemetry service layer.

Handles business logic for storing and retrieving telemetry data from TimescaleDB.
"""

from typing import Optional

from sqlalchemy.orm import Session

from src.infrastructure.db.database import db
from src.repository.telemetry_repository import TelemetryRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TelemetryService:
    """Service for telemetry business logic."""

    def __init__(self, session: Optional[Session] = None):
        """Initialize service with optional TimescaleDB session."""
        self.session = session or db.get_timescale_session()
        self.repo = TelemetryRepository(self.session)

    def store_telemetry(
        self,
        device_id: str,
        payload: dict,
    ) -> None:
        """
        Store telemetry data from device.

        Parses payload and extracts metrics (temperature, humidity, pressure).
        Stores each metric in TimescaleDB.

        Args:
            device_id: Device identifier
            payload: Telemetry payload from device

        Example payload:
            {
                "temperature": 24.5,
                "humidity": 65.2,
                "pressure": 1013.25,
                "metadata": {"location": "greenhouse"}
            }

        Raises:
            Exception: If storage fails
        """
        logger.debug("telemetry_storing", device_id=device_id)

        try:
            # Extract temperature, humidity, pressure
            temperature = payload.get("temperature")
            humidity = payload.get("humidity")
            pressure = payload.get("pressure")
            metadata = payload.get("metadata")
            
            # Validate that at least one metric is present
            if not any([temperature, humidity, pressure]):
                logger.warning(
                    "telemetry_no_metrics",
                    device_id=device_id,
                    payload=payload,
                )
                return
            
            # Convert to float if present
            if temperature is not None:
                temperature = float(temperature)
            if humidity is not None:
                humidity = float(humidity)
            if pressure is not None:
                pressure = float(pressure)
            
            # Store in TimescaleDB
            self.repo.insert(
                device_id=device_id,
                temperature=temperature,
                humidity=humidity,
                pressure=pressure,
                metadata=metadata,
            )
            
            logger.info(
                "telemetry_stored",
                device_id=device_id,
                temperature=temperature,
                humidity=humidity,
                pressure=pressure,
            )

        except ValueError as e:
            logger.error(
                "telemetry_invalid_value",
                device_id=device_id,
                error=str(e),
            )
            raise
        except Exception as e:
            logger.error("telemetry_store_failed", device_id=device_id, error=str(e))
            raise

    def get_device_telemetry(
        self,
        device_id: str,
        metric_name: Optional[str] = None,
        limit: int = 100,
        hours: Optional[int] = None,
    ) -> list[dict]:
        """
        Get telemetry data for a device.

        Args:
            device_id: Device identifier
            metric_name: Optional specific metric ('temperature', 'humidity', 'pressure')
            limit: Maximum number of data points (default 100)
            hours: Optional time window in hours

        Returns:
            List of telemetry data points
        """
        try:
            if metric_name:
                # Get specific metric
                return self.repo.get_by_metric(
                    device_id=device_id,
                    metric=metric_name,
                    limit=limit,
                )
            else:
                # Get all metrics
                return self.repo.get_recent(
                    device_id=device_id,
                    limit=limit,
                    hours=hours,
                )
        except Exception as e:
            logger.error(
                "get_device_telemetry_failed",
                device_id=device_id,
                error=str(e),
            )
            raise

    def get_hourly_summary(
        self,
        device_id: str,
        hours: int = 24,
    ) -> list[dict]:
        """
        Get hourly aggregated telemetry summary.

        Uses pre-aggregated continuous aggregate for efficiency.

        Args:
            device_id: Device identifier
            hours: Number of hours to retrieve (default 24)

        Returns:
            List of hourly aggregated records with min/max/avg
        """
        try:
            return self.repo.get_hourly_rollup(
                device_id=device_id,
                hours=hours,
            )
        except Exception as e:
            logger.error(
                "get_hourly_summary_failed",
                device_id=device_id,
                error=str(e),
            )
            raise

    def close(self) -> None:
        """Close the session."""
        self.session.close()

