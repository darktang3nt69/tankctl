from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import EventLog
from typing import List
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import select

router = APIRouter()

class EventResponse(BaseModel):
    id: int
    tank_id: int
    event_type: str
    details: dict
    timestamp: datetime

@router.get("/", response_model=List[EventResponse])
async def list_events(
    tank_id: int = None,
    event_type: str = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List events with optional filtering."""
    query = select(EventLog)
    if tank_id:
        query = query.where(EventLog.tank_id == tank_id)
    if event_type:
        query = query.where(EventLog.event_type == event_type)
    query = query.order_by(EventLog.timestamp.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific event."""
    result = await db.execute(select(EventLog).where(EventLog.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.delete("/{event_id}")
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an event."""
    result = await db.execute(select(EventLog).where(EventLog.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.delete(event)
    await db.commit()
    return {"message": "Event deleted"} 