"""
Event API routes.

Provides endpoints for querying system events and device-specific events.
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from src.infrastructure.events.event_store import EventStore
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


class EventResponse(BaseModel):
    """Event response model."""
    
    event: str = Field(..., description="Event type")
    device_id: Optional[str] = Field(None, description="Associated device ID")
    timestamp: float = Field(..., description="Event timestamp (Unix epoch)")
    metadata: dict = Field(default_factory=dict, description="Event metadata")


@router.get("", response_model=list[EventResponse])
async def get_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
) -> list[EventResponse]:
    """
    Get system events.
    
    Supports filtering by event_type and device_id.
    Events are returned in reverse chronological order (newest first).
    
    Args:
        event_type: Optional event type filter
        device_id: Optional device ID filter
        limit: Maximum number of events (default 100, max 1000)
    
    Returns:
        List of events matching filters
    """
    try:
        store = EventStore()
        events = store.get_events(
            event_type=event_type,
            device_id=device_id,
            limit=limit,
        )
        store.close()
        
        return [
            EventResponse(
                event=e.event,
                device_id=e.device_id,
                timestamp=e.timestamp,
                metadata=e.metadata or {},
            )
            for e in events
        ]
    
    except Exception as e:
        logger.error("events_get_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve events")


@router.get("/devices/{device_id}", response_model=list[EventResponse])
async def get_device_events(
    device_id: str = Query(..., description="Device ID"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of events to return"),
) -> list[EventResponse]:
    """
    Get events for a specific device.
    
    Returns device-specific events in reverse chronological order (newest first).
    
    Args:
        device_id: Device ID to query
        limit: Maximum number of events (default 50, max 500)
    
    Returns:
        List of events for the device
    """
    try:
        if len(device_id) > 100:
            raise ValueError("Device ID too long")
        
        store = EventStore()
        events = store.get_device_events(
            device_id=device_id,
            limit=limit,
        )
        store.close()
        
        return [
            EventResponse(
                event=e.event,
                device_id=e.device_id,
                timestamp=e.timestamp,
                metadata=e.metadata or {},
            )
            for e in events
        ]
    
    except ValueError as e:
        logger.warning("invalid_device_id", device_id=device_id)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("device_events_get_failed", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve device events")


@router.get("/types", response_model=list[str])
async def get_event_types() -> list[str]:
    """
    Get available event types.
    
    Returns:
        List of supported event types
    """
    from src.domain.event import EventType
    
    return list(EventType.__args__)
