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