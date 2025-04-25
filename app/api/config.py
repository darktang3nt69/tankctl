from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Tank, Schedule
from app.core.auth import get_current_tank
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter()

class ScheduleUpdate(BaseModel):
    feed_time: str  # HH:MM format
    light_on: str   # HH:MM format
    light_off: str  # HH:MM format

@router.post("/config/update/{tank_id}")
def update_config(
    tank_id: int,
    schedule: ScheduleUpdate,
    tank: Tank = Depends(get_current_tank),
    db: Session = Depends(get_db)
):
    # Verify tank_id matches authenticated tank
    if tank.id != tank_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this tank's config"
        )
    
    # Update or create schedules
    feed_schedule = Schedule(
        tank_id=tank_id,
        action="feed",
        time=schedule.feed_time,
        days=[0,1,2,3,4,5,6]  # Every day
    )
    
    light_on_schedule = Schedule(
        tank_id=tank_id,
        action="light_on",
        time=schedule.light_on,
        days=[0,1,2,3,4,5,6]
    )
    
    light_off_schedule = Schedule(
        tank_id=tank_id,
        action="light_off",
        time=schedule.light_off,
        days=[0,1,2,3,4,5,6]
    )
    
    # Remove old schedules
    db.query(Schedule).filter(Schedule.tank_id == tank_id).delete()
    
    # Add new schedules
    db.add_all([feed_schedule, light_on_schedule, light_off_schedule])
    db.commit()
    
    return {"message": "Schedule updated successfully"}

@router.get("/config/{tank_id}")
def get_config(
    tank_id: int,
    tank: Tank = Depends(get_current_tank),
    db: Session = Depends(get_db)
):
    # Verify tank_id matches authenticated tank
    if tank.id != tank_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this tank's config"
        )
    
    schedules = db.query(Schedule)\
        .filter(Schedule.tank_id == tank_id)\
        .all()
    
    config = {
        "feed_time": next((s.time for s in schedules if s.action == "feed"), None),
        "light_on": next((s.time for s in schedules if s.action == "light_on"), None),
        "light_off": next((s.time for s in schedules if s.action == "light_off"), None)
    }
    
    return config