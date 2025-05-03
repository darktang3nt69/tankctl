# app/api/v1/override_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from uuid import UUID

from app.api.deps import get_db, verify_admin_api_key
from app.models.tank_settings import TankSettings
from app.services.tank_settings_service import set_manual_override

router = APIRouter(
    prefix="/tank/override",
    tags=["manual override"],
    dependencies=[Depends(verify_admin_api_key)],
)

class OverrideRequest(BaseModel):
    tank_id: UUID
    override_state: str = Field(..., regex="^(on|off|null)$", description="‘on’, ‘off’, or null to clear")

@router.post("", status_code=204)
def override_tank(req: OverrideRequest, db: Session = Depends(get_db)):
    # ensure row exists
    settings = db.get(TankSettings, req.tank_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Tank settings not found")
    # apply override
    set_manual_override(db, str(req.tank_id), None if req.override_state=="null" else req.override_state)
