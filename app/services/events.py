import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4

from app.core.redis import get_redis_pool

async def publish_event(
    event_type: str,
    data: Dict[str, Any],
    tank_id: Optional[str] = None
):
    """
    Publish an event to Redis for SSE distribution.
    
    Args:
        event_type: Type of event (status_change, command_issued, etc.)
        data: Event data
        tank_id: Optional tank ID for targeted events
    """
    redis = await get_redis_pool()
    
    # Create event payload
    event = {
        "id": str(uuid4()),
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }
    
    # Publish to specific tank channel if provided
    if tank_id:
        await redis.publish(f"tank:{tank_id}", json.dumps(event))
    
    # Always publish to all tanks channel
    await redis.publish("tanks:all", json.dumps(event))

# Define event types
class EventType:
    TANK_STATUS_CHANGE = "tank_status_change"
    TANK_OFFLINE = "tank_offline"
    TANK_ONLINE = "tank_online"
    COMMAND_ISSUED = "command_issued"
    COMMAND_ACKNOWLEDGED = "command_acknowledged"
    COMMAND_COMPLETED = "command_completed"
    COMMAND_FAILED = "command_failed"
    TEMPERATURE_ALERT = "temperature_alert"
    PH_ALERT = "ph_alert" 