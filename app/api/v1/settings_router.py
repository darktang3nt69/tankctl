from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_tank, get_db
from app.models.tank_settings import TankSettings
from app.schemas.tank import TankSettingsResponse
from sqlalchemy import select
from uuid import UUID

router = APIRouter()

@router.get("/tank/settings")
def get_tank_settings(
    db: Session = Depends(get_db),
    tank_id: UUID = Depends(get_current_tank),
):
    settings = db.execute(
        select(TankSettings).where(TankSettings.tank_id == tank_id)
    ).scalar_one_or_none()

    if not settings:
        raise HTTPException(status_code=404, detail="Tank settings not found")

    return settings
