# app/api/v1/settings_router.py

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, verify_admin_api_key
from app.models.tank import Tank
from app.schemas.tank_settings import (
    TankSettingsResponse,
    TankSettingsUpdateRequest,
    TankOverrideRequest,
)
from app.services.tank_settings_service import (
    get_or_create_settings,
    update_tank_settings,
    manual_override_command,
)
from app.utils.discord import send_discord_embed

router = APIRouter(
    prefix="/tank/settings",
    tags=["tank settings"],
    dependencies=[Depends(verify_admin_api_key)],  # require x‑api‑key header
)


def _ensure_tank_exists(db: Session, tank_id: str):
    """Raise 404 if no Tank row with this ID."""
    if not db.get(Tank, tank_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tank '{tank_id}' not found.",
        )


@router.get(
    "",
    response_model=TankSettingsResponse,
    summary="(Admin) Fetch a tank's lighting settings",
)
def read_settings(
    *,
    tank_id: UUID = Query(..., description="UUID of the tank"),
    db: Session = Depends(get_db),
):
    _ensure_tank_exists(db, str(tank_id))
    return get_or_create_settings(db, str(tank_id))


@router.put(
    "",
    response_model=TankSettingsResponse,
    summary="(Admin) Update a tank's lighting schedule",
)
def put_settings(
    *,
    payload: TankSettingsUpdateRequest,
    db: Session = Depends(get_db),
):
    _ensure_tank_exists(db, str(payload.tank_id))
    try:
        # update_tank_settings now also clears any outstanding pause
        return update_tank_settings(db, str(payload.tank_id), payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/override",
    response_model=TankSettingsResponse,
    summary="(Admin) Manually override lights ON or OFF",
)
def post_manual_override(
    *,
    payload: TankOverrideRequest,
    db: Session = Depends(get_db),
):
    """
    Provide {"tank_id": "<uuid>", "override_command": "on"|"off"}
    to fire the corresponding light_on/light_off immediately
    and pause automated scheduling until the next schedule edge.
    """
    tank_id = str(payload.tank_id)
    _ensure_tank_exists(db, tank_id)
    return manual_override_command(db, payload)


@router.post(
    "/override/clear",
    response_model=TankSettingsResponse,
    summary="(Admin) Clear any manual lighting pause and resume schedule immediately",
)
def clear_manual_override(
    *,
    tank_id: UUID = Query(..., description="UUID of the tank"),
    db: Session = Depends(get_db),
):
    """
    Force‑clear any outstanding pause (schedule_paused_until),
    reset today's schedule markers, and resume normal scheduling.
    """
    tid = str(tank_id)
    _ensure_tank_exists(db, tid)

    settings = get_or_create_settings(db, tid)

    # nothing to do?
    if settings.schedule_paused_until is None:
        return settings

    # clear the pause and today's markers
    settings.schedule_paused_until   = None
    settings.last_schedule_check_on  = None
    settings.last_schedule_check_off = None

    db.add(settings)
    db.commit()
    db.refresh(settings)

    send_discord_embed(
        status="override_cleared",
        tank_name=settings.tank.tank_name,
        command_payload="Pause cleared via API"
    )

    return settings
