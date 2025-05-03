from sqlalchemy.orm import Session
from app.models.tank_settings import TankSettings
from app.schemas.tank_settings import TankSettingsUpdateRequest, TankOverrideRequest
from app.utils.discord import send_discord_embed

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

    # patch only if provided
    if payload.light_on is not None:
        settings.light_on = payload.light_on
    if payload.light_off is not None:
        settings.light_off = payload.light_off
    if payload.is_schedule_enabled is not None:
        settings.is_schedule_enabled = payload.is_schedule_enabled

    db.add(settings)
    db.commit()
    db.refresh(settings)

    # fire off a Discord embed so you see the change
    extra = {
        "Tank ID":            str(settings.tank_id),
        "Light On (IST)":     settings.light_on.strftime("%H:%M"),
        "Light Off (IST)":    settings.light_off.strftime("%H:%M"),
        "Schedule Enabled?":  settings.is_schedule_enabled,
    }
    send_discord_embed(
        status="info",
        tank_name=settings.tank.tank_name,
        extra_fields=extra
    )

    return settings

def set_manual_override(
    db: Session,
    tank_id: str,
    state: str,  # “on” or “off”
) -> TankSettings:
    settings = get_or_create_settings(db, tank_id)
    settings.manual_override_state = state

    # clear today's schedule checks so next window still fires
    settings.last_schedule_check_on  = None
    settings.last_schedule_check_off = None

    db.add(settings)
    db.commit()
    db.refresh(settings)

    send_discord_embed(
        status=f"manual_light_{state}",
        tank_name=settings.tank.tank_name,
        extra_fields={
            "Tank ID": str(settings.tank_id),
            "Override": state.upper(),
        }
    )
    return settings
