# app/api/v1/settings_router.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.schemas.tank_settings import TankSettingsResponse, TankSettingsUpdateRequest
from app.services.tank_settings_service import (
    get_or_create_settings,
    update_tank_settings,
)
from app.api.deps import get_db, verify_admin_api_key

router = APIRouter(
    prefix="/tank/settings",
    tags=["tank settings"],
    dependencies=[Depends(verify_admin_api_key)],
)

@router.get(
    "",
    response_model=TankSettingsResponse,
    summary="(Admin) Fetch a tank's lighting settings",
)
def read_settings(
    tank_id: str = Query(..., description="UUID of the tank"),
    db: Session = Depends(get_db),
):
    """
    Query parameter `tank_id` must be provided.
    """
    settings = get_or_create_settings(db, tank_id)
    return settings

@router.put(
    "",
    response_model=TankSettingsResponse,
    summary="(Admin) Update a tank's lighting schedule",
)
def put_settings(
    payload: TankSettingsUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    JSON body must include:
      - tank_id
      - light_on (HH:MM)
      - light_off (HH:MM)
      - is_schedule_enabled (optional)
    """
    try:
        settings = update_tank_settings(
            db,
            tank_id=payload.tank_id,
            payload=payload  # will ignore extra fields automatically
        )
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
