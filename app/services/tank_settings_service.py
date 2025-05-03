# app/services/tank_settings_service.py

from sqlalchemy.orm import Session
from app.models.tank_settings import TankSettings
from app.schemas.tank_settings import TankSettingsUpdateRequest

def get_or_create_settings(db: Session, tank_id: str) -> TankSettings:
    settings = db.get(TankSettings, tank_id)
    if not settings:
        settings = TankSettings(tank_id=tank_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

def update_tank_settings(
    db: Session,
    tank_id: str,
    payload: TankSettingsUpdateRequest
) -> TankSettings:
    settings = get_or_create_settings(db, tank_id)
    settings.light_on = payload.light_on
    settings.light_off = payload.light_off
    if payload.is_schedule_enabled is not None:
        settings.is_schedule_enabled = payload.is_schedule_enabled
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings
