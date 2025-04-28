# app/services/status_service.py

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.tank import Tank
from app.models.status_log import StatusLog
from app.schemas.status import StatusUpdateRequest, StatusUpdateResponse
from app.utils.timezone import IST

def update_tank_status(db: Session, tank_id: str, request: StatusUpdateRequest) -> StatusUpdateResponse:
    tank = db.execute(
        select(Tank).where(Tank.tank_id == tank_id)
    ).scalar_one_or_none()

    if not tank:
        raise ValueError(f"Tank with id={tank_id} not found.")

    # Update heartbeat
    now = datetime.now(IST)
    tank.last_seen = now

    # Update optional fields
    if request.temperature is not None:
        tank.temperature = request.temperature
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
        timestamp=now.isoformat()  # ✅ Add timestamp
    )
