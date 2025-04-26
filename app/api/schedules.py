from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.crud import get_all_tanks
from app.db.models import Schedule
from typing import List
from uuid import UUID
from pydantic import BaseModel
from datetime import time

router = APIRouter()

class ScheduleCreate(BaseModel):
    tank_id: UUID
    command: str
    parameters: dict
    time: time
    days: List[int]  # 0-6 for Monday-Sunday
    enabled: bool = True

class ScheduleResponse(ScheduleCreate):
    id: UUID

@router.post("/", response_model=ScheduleResponse)
async def create_schedule(schedule: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new schedule for a tank."""
    tanks = await get_all_tanks()
    if not any(t.id == schedule.tank_id for t in tanks):
        raise HTTPException(status_code=404, detail="Tank not found")
    
    new_schedule = Schedule(**schedule.dict())
    db.add(new_schedule)
    await db.commit()
    await db.refresh(new_schedule)
    return new_schedule

@router.get("/", response_model=List[ScheduleResponse])
async def list_schedules(db: AsyncSession = Depends(get_db)):
    """List all schedules."""
    result = await db.execute(select(Schedule))
    return result.scalars().all()

@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific schedule."""
    schedule = await db.get(Schedule, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule

@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a schedule."""
    schedule = await db.get(Schedule, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await db.delete(schedule)
    await db.commit()
    return {"message": "Schedule deleted"} 