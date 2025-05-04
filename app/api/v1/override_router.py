# app/api/v1/override_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, verify_admin_api_key
from app.models.tank_settings import TankSettings
from app.schemas.tank_settings import TankSettingsResponse, TankOverrideRequest
from app.services.tank_settings_service import manual_override_command

router = APIRouter(
    prefix="/tank/override",
    tags=["manual override"],
)

@router.post(
    "",
    response_model=TankSettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="(Admin) Manually override lights ON/OFF for a tank",
    dependencies=[Depends(verify_admin_api_key)],  # require x-api-key
)
def override_tank(
    req: TankOverrideRequest,
    db: Session = Depends(get_db),
):
    # 1) ensure the tank has settings
    settings = db.get(TankSettings, req.tank_id)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tank settings not found",
        )

    # 2) apply manual override (payload.override_command is 'light_on' or 'light_off')
    updated = manual_override_command(db, req)

    # 3) return the updated settings record
    return updated
