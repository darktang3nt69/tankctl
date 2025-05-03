# app/api/v1/settings_router.py

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.schemas.tank_settings import (
    TankSettingsResponse,
    TankSettingsUpdateRequest,
)
from app.services.tank_settings_service import (
    get_or_create_settings,
    update_tank_settings,
)
from app.api.deps import get_db, verify_admin_api_key
from app.models.tank import Tank


router = APIRouter(
    prefix="/tank/settings",
    tags=["tank settings"],
    dependencies=[Depends(verify_admin_api_key)],  # requires x-api-key
)


def _ensure_tank_exists(db: Session, tank_id: str):
    """Raise 404 if no Tank row with this ID."""
    exists = db.query(Tank).get(tank_id)
    if not exists:
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
    tank_id: str = Query(..., description="UUID of the tank"),
    db: Session = Depends(get_db),
):
    # 1) make sure the tank exists
    _ensure_tank_exists(db, tank_id)

    # 2) fetch or create its settings (won't blow up FK since we know the tank is there)
    settings = get_or_create_settings(db, tank_id)
    return settings


@router.put(
    "",
    response_model=TankSettingsResponse,
    summary="(Admin) Update a tank's lighting schedule",
)
def put_settings(
    *,
    tank_id: str = Query(..., description="UUID of the tank"),
    payload: TankSettingsUpdateRequest,
    db: Session = Depends(get_db),
):
    # 1) guard the tank exists
    _ensure_tank_exists(db, tank_id)

    # 2) apply the update (won't blow up FK now)
    try:
        updated = update_tank_settings(db, tank_id, payload)
        return updated

    except Exception as e:
        # you might want to catch more specific exceptions here
        raise HTTPException(status_code=500, detail=str(e))
