"""
Event store for persisting events to database.

Provides event history and audit trail.
"""

import json
from typing import Optional

from src.infrastructure.db.database import db
from src.infrastructure.db.models import EventRecord
from src.domain.event import Event
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EventStore:
    """Event storage and retrieval."""
    
    def __init__(self, session=None):
        """Initialize event store."""
        self.session = session or db.get_session()
    
    def store_event(self, event: Event) -> Optional[EventRecord]:
        """
        Store event in database.
        
        Args:
            event: Event to store
        
        Returns:
            Stored EventRecord or None if failed
        """
        try:
            metadata_json = json.dumps(event.metadata) if event.metadata else None
            
            record = EventRecord(
                event=event.event,
                device_id=event.device_id,
                timestamp=event.timestamp,
                event_metadata=metadata_json,
            )
            
            self.session.add(record)
            self.session.commit()
            
            logger.debug(f"Event stored: {event.event}")
            return record
        
        except Exception as e:
            logger.error(f"Failed to store event: {e}")
            self.session.rollback()
            return None
    
    def get_events(
        self,
        event_type: Optional[str] = None,
        device_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[Event]:
        """
        Get events from storage.
        
        Args:
            event_type: Filter by event type
            device_id: Filter by device
            limit: Maximum number of events
        
        Returns:
            List of events
        """
        try:
            query = self.session.query(EventRecord)
            
            if event_type:
                query = query.filter(EventRecord.event == event_type)
            
            if device_id:
                query = query.filter(EventRecord.device_id == device_id)
            
            records = query.order_by(EventRecord.timestamp.desc()).limit(limit).all()
            
            return [r.to_domain() for r in records]
        
        except Exception as e:
            logger.error(f"Failed to retrieve events: {e}")
            return []
    
    def get_device_events(self, device_id: str, limit: int = 50) -> list[Event]:
        """
        Get events for a specific device.
        
        Args:
            device_id: Device ID
            limit: Maximum number of events
        
        Returns:
            List of events for device
        """
        return self.get_events(device_id=device_id, limit=limit)
    
    def close(self) -> None:
        """Close database session."""
        self.session.close()


# Event store handler for use with publisher
def event_store_handler(event: Event) -> None:
    """Handler to store events in database."""
    try:
        store = EventStore()
        store.store_event(event)
        store.close()
    except Exception as e:
        logger.error(f"Event store handler error: {e}")
