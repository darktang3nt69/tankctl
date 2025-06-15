# app/services/status_service.py

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.tank import Tank
from app.models.status_log import StatusLog
from app.schemas.status import StatusUpdateRequest, StatusUpdateResponse
from app.utils.timezone import IST
from app.metrics.tank_metrics import tank_temperature
from app.services.push_notification import send_tank_notification
import asyncio

def update_tank_status(db: Session, tank_id: str, request: StatusUpdateRequest) -> StatusUpdateResponse:
    tank = db.execute(
        select(Tank).where(Tank.tank_id == tank_id)
    ).scalar_one_or_none()

    if not tank:
        print(f"[ERROR] Tank not found in DB. tank_id={tank_id}")
        raise ValueError(f"Tank with id={tank_id} not found.")

    # Update heartbeat
    now = datetime.now(IST)
    tank.last_seen = now

    # Update optional fields
    if request.temperature is not None:
        tank.temperature = request.temperature
        # Update Prometheus metric with location
        # Refer to Prometheus documentation for best practices on metrics: https://prometheus.io/docs/practices/instrumentation/
        tank_temperature.labels(
            tank_name=tank.tank_name,
            location=tank.location or "unknown"
        ).set(request.temperature)

        # Add temperature alert logic
        if request.temperature > 32:
            asyncio.run(send_tank_notification(
                tank_id=tank_id,
                title="Temperature Alert: High",
                body=f"Tank {tank.tank_name} temperature is {request.temperature}°C, which is above the safe threshold.",
                notification_type="temperature_alert",
                icon="/icons/temperature-alert.png",
                badge="/icons/badge-alert.png",
                tag=f"temp-alert-high-{tank_id}"
            ))
    if request.ph is not None:
        tank.ph = request.ph
    if request.light_state is not None:
        tank.light_state = request.light_state
    if request.firmware_version is not None:
        tank.firmware_version = request.firmware_version

    # Log status history
    status_log = StatusLog(
        tank_id=tank.tank_id,
        timestamp=now,
        temperature=request.temperature,
        ph=request.ph,
        light_state=request.light_state,
        firmware_version=request.firmware_version,
    )
    db.add(status_log)

    db.commit()

    return StatusUpdateResponse(
        message="Tank status updated successfully",
        tank_id=str(tank.tank_id),
        timestamp=now.isoformat()
    )
