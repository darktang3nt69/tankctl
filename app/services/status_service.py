from datetime import datetime
from sqlalchemy.orm import Session

from app.models.tank import Tank
from app.models.status_log import StatusLog
from app.schemas.status import StatusUpdateRequest, StatusUpdateResponse

def update_tank_status(
    db: Session,
    tank_id: str,
    request: StatusUpdateRequest
) -> StatusUpdateResponse:
    # 1) Fetch the tank
    tank = db.get(Tank, tank_id)
    if not tank:
        raise KeyError("Tank not found")

    # 2) Update its last_seen and online status
    now = datetime.utcnow()
    tank.last_seen = now
    tank.is_online = True

    # 3) Record the StatusLog
    status_entry = StatusLog(
        tank_id=tank_id,
        timestamp=now,
        temperature=request.temperature,
        ph=request.ph,
        light_state=request.light_state,
        firmware_version=request.firmware_version,
    )
    db.add(status_entry)

    # 4) Persist changes
    db.commit()

    # 5) Respond
    return StatusUpdateResponse(
        message="Status updated successfully ✅",
        timestamp=now
    )
