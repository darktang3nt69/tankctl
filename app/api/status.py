from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Tank, TankStatus
from app.core.auth import get_current_tank
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, UTC

router = APIRouter()

class StatusUpdate(BaseModel):
    status: dict

class TankStatusResponse(BaseModel):
    id: int
    tank_id: int
    timestamp: datetime
    status: dict

@router.post("/status")
def update_status(
    status_update: StatusUpdate,
    tank: Tank = Depends(get_current_tank),
    db: Session = Depends(get_db)
):
    # Update tank's last_seen time
    tank.last_seen = datetime.now(UTC)
    
    # Create new status entry
    new_status = TankStatus(
        tank_id=tank.id,
        status=status_update.status
    )
    db.add(new_status)
    db.commit()
    db.refresh(new_status)
    
    return {"message": "Status updated successfully"}

@router.get("/status/all", response_model=List[TankStatusResponse])
def get_all_statuses(
    limit: Optional[int] = 100,
    db: Session = Depends(get_db)
):
    statuses = db.query(TankStatus)\
        .order_by(TankStatus.timestamp.desc())\
        .limit(limit)\
        .all()
    return statuses

@router.get("/status/{tank_name}", response_model=List[TankStatusResponse])
def get_tank_status(
    tank_name: str,
    limit: Optional[int] = 100,
    tank: Tank = Depends(get_current_tank),
    db: Session = Depends(get_db)
):
    # Verify tank_name matches authenticated tank
    if tank.name != tank_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this tank's status"
        )
    
    statuses = db.query(TankStatus)\
        .filter(TankStatus.tank_id == tank.id)\
        .order_by(TankStatus.timestamp.desc())\
        .limit(limit)\
        .all()
    return statuses