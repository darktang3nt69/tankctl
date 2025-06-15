from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import StreamingResponse
from app.api.deps import get_current_user # Assuming get_current_user is still needed for SSE auth
import asyncio
import json
import logging
from typing import AsyncGenerator, Optional
from uuid import uuid4

from app.core.redis import get_redis_pool # Import the Redis connection pool

router = APIRouter()

logger = logging.getLogger(__name__)

def format_sse_event(data: dict, event: Optional[str] = None, id: Optional[str] = None) -> str:
    """Format data as SSE event string"""
    message = ""
    
    if id is not None:
        message += f"id: {id}\n"
    
    if event is not None:
        message += f"event: {event}\n"
    
    message += f"data: {json.dumps(data)}\n\n"
    return message

@router.get("/events")
async def event_stream(
    request: Request,
    tank_id: Optional[str] = None,
    event_type: Optional[str] = None,
    # current_user = Depends(get_current_user) # Removed authentication
):
    """
    Server-Sent Events (SSE) endpoint for real-time updates.
    
    Args:
        request: The FastAPI request object
        tank_id: Optional tank ID to filter events
        event_type: Optional event type to filter events
        current_user: The authenticated user
        
    Returns:
        StreamingResponse: SSE stream
    """
    client_id = str(uuid4())
    logger.info(f"SSE connection established: {client_id}")

    async def event_generator() -> AsyncGenerator[str, None]:
        redis = await get_redis_pool()
        pubsub = redis.pubsub()
        
        channels = []
        if tank_id:
            channels.append(f"tank:{tank_id}")
        else:
            channels.append("tanks:all")
        
        # Add event type specific channels if needed
        if event_type:
            channels.append(f"event:{event_type}")

        await pubsub.subscribe(*channels)
        
        try:
            yield format_sse_event(
                data={"message": "Connection established", "client_id": client_id},
                event="connection_established"
            )
            
            while True:
                if await request.is_disconnected():
                    logger.info(f"SSE client disconnected: {client_id}")
                    break
                
                message = await pubsub.get_message(timeout=25) # Shorter than 30s to ensure keepalive

                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    
                    if event_type and data.get("event_type") != event_type:
                        continue
                    
                    yield format_sse_event(
                        data=data,
                        event=data.get("event_type", "message"),
                        id=data.get("id")
                    )
                    logger.debug(f"Successfully sent SSE event: {{data.get('event_type', 'message')}} (ID: {{data.get('id')}})")
                else:
                    # If no message within timeout, send a keepalive comment
                    yield ": keepalive\n\n" # Yield the keepalive comment directly
                
                await asyncio.sleep(0.1)
        finally:
            await pubsub.unsubscribe(*channels)
            await redis.close()
            logger.info(f"SSE connection closed: {client_id}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/events/docs", tags=["documentation"])
async def events_documentation():
    """
    Server-Sent Events (SSE) documentation for frontend developers.
    
    This endpoint provides detailed information about the SSE endpoint,
    event types, and example code for handling events in the frontend.
    
    Event endpoint: /api/v1/events
    
    Query parameters:
    - tank_id (optional): Filter events by tank ID
    - event_type (optional): Filter events by type
    - since (optional): Get events since timestamp (ISO format)
    
    Event types:
    - tank_status_change: Tank status has been updated
    - tank_offline: Tank has gone offline
    - tank_online: Tank has come back online
    - command_issued: New command has been issued
    - command_acknowledged: Command has been acknowledged by tank
    - command_completed: Command has been completed successfully
    - command_failed: Command execution failed
    - temperature_alert: Temperature is outside normal range
    - ph_alert: pH is outside normal range
    
    Event format:
    ```
    event: [event_type]
    id: [unique_event_id]
    data: {
        "timestamp": "2025-06-12T10:30:00Z",
        "tank_id": "tank-123",
        ... event specific data ...
    }
    ```
    
    Example frontend code:
    ```javascript
    function connectToEventStream() {
      const token = sessionStorage.getItem('token');
      const eventSource = new EventSource(`/api/v1/events?tank_id=${tankId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      // Handle connection established
      eventSource.addEventListener('connection_established', (event) => {
        console.log('SSE connection established');
      });
      
      // Handle tank status changes
      eventSource.addEventListener('tank_status_change', (event) => {
        const data = JSON.parse(event.data);
        updateTankStatus(data);
      });
      
      // Handle tank offline events
      eventSource.addEventListener('tank_offline', (event) => {
        const data = JSON.parse(event.data);
        showOfflineAlert(data);
      });
      
      // Handle command events
      eventSource.addEventListener('command_completed', (event) => {
        const data = JSON.parse(event.data);
        updateCommandStatus(data);
      });
      
      // Handle connection errors
      eventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
        setTimeout(connectToEventStream, 5000); // Reconnect after 5 seconds
      };
      
      return eventSource;
    }
    ```
    
    Reconnection strategy:
    - If connection is lost, wait 5 seconds before reconnecting
    - Use exponential backoff for repeated failures
    - Store last event ID and use it when reconnecting to resume from where you left off
    """
    return {
        "endpoint": "/api/v1/events",
        "query_parameters": {
            "tank_id": "Filter events by tank ID",
            "event_type": "Filter events by type",
            "since": "Get events since timestamp (ISO format)"
        },
        "event_types": {
            "tank_status_change": "Tank status has been updated",
            "tank_offline": "Tank has gone offline",
            "tank_online": "Tank has come back online",
            "command_issued": "New command has been issued",
            "command_acknowledged": "Command has been acknowledged by tank",
            "command_completed": "Command has been completed successfully",
            "command_failed": "Command execution failed",
            "temperature_alert": "Temperature is outside normal range",
            "ph_alert": "pH is outside normal range"
        },
        "event_format": {
            "example": 'event: tank_status_change\nid: 123\ndata: {"timestamp": "2025-06-12T10:30:00Z", "tank_id": "tank-123", "temperature": 25.5}'
        },
        "reconnection_strategy": {
            "initial_delay": "5 seconds",
            "backoff": "Exponential",
            "resume": "Use last event ID when reconnecting"
        }
    } 