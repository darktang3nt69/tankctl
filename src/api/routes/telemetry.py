"""
Telemetry Routes - Telemetry data retrieval endpoints.

GET /devices/{device_id}/telemetry - Get latest telemetry data
GET /devices/{device_id}/telemetry/{metric} - Get specific metric
GET /devices/{device_id}/telemetry/hourly - Get hourly summary
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from src.infrastructure.db.database import db
from src.services.telemetry_service import TelemetryService
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/devices", tags=["telemetry"])


def get_db_telemetry():
    """Dependency: Get TimescaleDB session for telemetry."""
    session = db.get_timescale_session()
    try:
        yield session
    finally:
        session.close()


@router.get("/{device_id}/telemetry", response_model=dict)
def get_telemetry(
    device_id: str,
    limit: int = 100,
    hours: int = None,
    session: Session = Depends(get_db_telemetry)
):
    """
    Get latest telemetry data for device.

    Args:
        device_id: Device ID
        limit: Maximum number of data points (default 100)
        hours: Optional time window in hours

    Returns:
        List of telemetry data points with timestamp and metrics
        
    Example response:
        {
            "device_id": "tank1",
            "count": 10,
            "data": [
                {
                    "time": "2025-01-15T10:30:00+00:00",
                    "device_id": "tank1",
                    "temperature": 24.5,
                    "humidity": 65.2,
                    "pressure": null,
                    "metadata": null
                }
            ]
        }
    """
    try:
        # Validate inputs
        if limit < 1 or limit > 10000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 10000")
        
        if hours is not None and hours < 1:
            raise HTTPException(status_code=400, detail="Hours must be >= 1")
        
        logger.debug("getting_telemetry", device_id=device_id, limit=limit, hours=hours)
        
        telemetry_service = TelemetryService(session)
        data = telemetry_service.get_device_telemetry(
            device_id=device_id,
            limit=limit,
            hours=hours,
        )
        
        logger.info("telemetry_retrieved", device_id=device_id, count=len(data))
        
        return {
            "device_id": device_id,
            "count": len(data),
            "data": data,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_telemetry_error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{device_id}/telemetry/{metric}", response_model=dict)
def get_metric(
    device_id: str,
    metric: str,
    limit: int = 100,
    session: Session = Depends(get_db_telemetry)
):
    """
    Get specific metric data for device.

    Args:
        device_id: Device ID
        metric: Metric name ('temperature', 'humidity', or 'pressure')
        limit: Maximum number of data points (default 100)

    Returns:
        List of metric data points
        
    Example response:
        {
            "device_id": "tank1",
            "metric": "temperature",
            "count": 10,
            "data": [
                {
                    "time": "2025-01-15T10:30:00+00:00",
                    "device_id": "tank1",
                    "value": 24.5
                }
            ]
        }
    """
    try:
        # Validate metric name
        if metric not in ("temperature", "humidity", "pressure"):
            raise HTTPException(
                status_code=400,
                detail="Metric must be 'temperature', 'humidity', or 'pressure'"
            )
        
        if limit < 1 or limit > 10000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 10000")
        
        logger.debug(
            "getting_metric",
            device_id=device_id,
            metric=metric,
            limit=limit
        )
        
        telemetry_service = TelemetryService(session)
        data = telemetry_service.get_device_telemetry(
            device_id=device_id,
            metric_name=metric,
            limit=limit,
        )
        
        logger.info(
            "metric_retrieved",
            device_id=device_id,
            metric=metric,
            count=len(data)
        )
        
        return {
            "device_id": device_id,
            "metric": metric,
            "count": len(data),
            "data": data,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_metric_error",
            device_id=device_id,
            metric=metric,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{device_id}/telemetry/hourly/summary", response_model=dict)
def get_hourly_summary(
    device_id: str,
    hours: int = 24,
    session: Session = Depends(get_db_telemetry)
):
    """
    Get hourly aggregated telemetry summary.

    Uses pre-aggregated continuous aggregate for fast dashboard queries.

    Args:
        device_id: Device ID
        hours: Number of hours to retrieve (default 24)

    Returns:
        List of hourly aggregated records with min/max/avg statistics
        
    Example response:
        {
            "device_id": "tank1",
            "count": 24,
            "data": [
                {
                    "hour": "2025-01-14T10:00:00+00:00",
                    "device_id": "tank1",
                    "temperature": {
                        "avg": 24.2,
                        "max": 25.1,
                        "min": 23.5
                    },
                    "humidity": {
                        "avg": 63.5,
                        "max": 68.2,
                        "min": 60.1
                    },
                    "sample_count": 120
                }
            ]
        }
    """
    try:
        if hours < 1 or hours > 8760:  # Max 1 year
            raise HTTPException(status_code=400, detail="Hours must be between 1 and 8760")
        
        logger.debug("getting_hourly_summary", device_id=device_id, hours=hours)
        
        telemetry_service = TelemetryService(session)
        data = telemetry_service.get_hourly_summary(
            device_id=device_id,
            hours=hours,
        )
        
        logger.info("hourly_summary_retrieved", device_id=device_id, count=len(data))
        
        return {
            "device_id": device_id,
            "count": len(data),
            "data": data,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_hourly_summary_error",
            device_id=device_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Internal server error")

