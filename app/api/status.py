from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
async def update_status(
    status_update: StatusUpdate,
    tank: Tank = Depends(get_current_tank),
    db: AsyncSession = Depends(get_db)
):
    # Update tank's last_seen time
    tank.last_seen = datetime.now(UTC)
    
    # Update tank metrics
    if "temperature" in status_update.status:
        tank.temperature = status_update.status["temperature"]
    if "humidity" in status_update.status:
        tank.humidity = status_update.status["humidity"]
    if "water_level" in status_update.status:
        tank.water_level = status_update.status["water_level"]
    if "ph" in status_update.status:
        tank.ph_level = status_update.status["ph"]
    
    # Create new status entry
    new_status = TankStatus(
        tank_id=tank.id,
        status=status_update.status
    )
    db.add(new_status)
    await db.commit()
    await db.refresh(new_status)
    
    return {"message": "Status updated successfully"}

@router.get("/status/all", response_model=List[TankStatusResponse])
async def get_all_statuses(
    limit: Optional[int] = 100,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(TankStatus)
        .order_by(TankStatus.timestamp.desc())
        .limit(limit)
    )
    statuses = result.scalars().all()
    return statuses

@router.get("/status/{tank_name}", response_model=List[TankStatusResponse])
async def get_tank_status(
    tank_name: str,
    limit: Optional[int] = 100,
    tank: Tank = Depends(get_current_tank),
    db: AsyncSession = Depends(get_db)
):
    # Verify tank_name matches authenticated tank
    if tank.name != tank_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this tank's status"
        )
    
    result = await db.execute(
        select(TankStatus)
        .where(TankStatus.tank_id == tank.id)
        .order_by(TankStatus.timestamp.desc())
        .limit(limit)
    )
    statuses = result.scalars().all()
    return statuses