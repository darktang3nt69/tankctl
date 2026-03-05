"""
Event publisher for TankCtl.

Provides centralized event publishing and subscription.
"""

from typing import Callable, List, Dict
from src.domain.event import Event, EventType
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EventPublisher:
    """Centralized event publisher."""
    
    def __init__(self):
        """Initialize event publisher."""
        self.subscribers: Dict[EventType, List[Callable[[Event], None]]] = {}
        self.all_subscribers: List[Callable[[Event], None]] = []
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """
        Subscribe to a specific event type.
        
        Args:
            event_type: Event type to subscribe to
            handler: Callable that handles the event
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
        logger.debug(f"Subscribed to event: {event_type}")
    
    def subscribe_all(self, handler: Callable[[Event], None]) -> None:
        """
        Subscribe to all event types.
        
        Args:
            handler: Callable that handles any event
        """
        self.all_subscribers.append(handler)
        logger.debug("Subscribed to all events")
    
    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """
        Unsubscribe from a specific event type.
        
        Args:
            event_type: Event type to unsubscribe from
            handler: The handler to remove
        """
        if event_type in self.subscribers:
            if handler in self.subscribers[event_type]:
                self.subscribers[event_type].remove(handler)
                logger.debug(f"Unsubscribed from event: {event_type}")
    
    def publish(self, event: Event) -> None:
        """
        Publish an event.
        
        Args:
            event: Event to publish
        """
        logger.info(str(event))
        
        # Call all subscribers
        for handler in self.all_subscribers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}", exc_info=True)
        
        # Call specific event type subscribers
        if event.event in self.subscribers:
            for handler in self.subscribers[event.event]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Event handler error: {e}", exc_info=True)


# Singleton instance
event_publisher = EventPublisher()
