from typing import Dict, Any, List, Optional
import json
from pywebpush import webpush, WebPushException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.push_subscription import PushSubscription
from app.core.database import get_db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def send_push_notification(
    subscription: PushSubscription,
    title: str,
    body: str,
    icon: Optional[str] = None,
    badge: Optional[str] = None,
    tag: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    actions: Optional[List[Dict[str, str]]] = None,
    url: Optional[str] = None
) -> bool:
    """
    Send a push notification to a specific subscription.
    
    Args:
        subscription: The push subscription object
        title: Notification title
        body: Notification body text
        icon: Optional URL to an icon image
        badge: Optional URL to a badge image
        tag: Optional tag for notification grouping
        data: Optional data to include with the notification
        actions: Optional list of actions (buttons)
        url: Optional URL to open when notification is clicked
        
    Returns:
        bool: Whether the notification was sent successfully
    """
    try:
        payload = {
            "notification": {
                "title": title,
                "body": body,
                "icon": icon,
                "badge": badge,
                "tag": tag,
                "data": data or {},
                "actions": actions or [],
                "requireInteraction": True
            }
        }
        
        if url:
            payload["notification"]["data"]["url"] = url
        
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh,
                    "auth": subscription.auth
                }
            },
            data=json.dumps(payload),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={
                "sub": f"mailto:{settings.VAPID_CLAIMS_EMAIL}"
            }
        )
        
        return True
    except WebPushException as e:
        logger.error(f"Push notification failed: {str(e)}")
        
        # Check if subscription is expired or invalid
        if e.response and e.response.status_code in (404, 410):
            # Remove invalid subscription
            db = next(get_db())
            try:
                db.delete(subscription)
                db.commit()
                logger.info(f"Removed invalid subscription: {subscription.endpoint}")
            except Exception as db_error:
                logger.error(f"Failed to remove invalid subscription: {str(db_error)}")
            finally:
                db.close()
        
        return False
    except Exception as e:
        logger.error(f"Push notification error: {str(e)}")
        return False

async def should_send_notification(subscription: PushSubscription, notification_type: str) -> bool:
    """
    Check if a notification should be sent based on user preferences.
    
    Args:
        subscription: The push subscription
        notification_type: Type of notification
        
    Returns:
        bool: Whether the notification should be sent
    """
    preferences = subscription.preferences
    
    # Check if this notification type is disabled
    if preferences.get(f"disable_{notification_type}", False):
        return False
    
    # Check quiet hours
    quiet_start = preferences.get("quiet_hours_start")
    quiet_end = preferences.get("quiet_hours_end")
    
    if quiet_start is not None and quiet_end is not None:
        current_hour = datetime.utcnow().hour
        
        # Handle wrap-around (e.g., 22:00 - 06:00)
        if quiet_start > quiet_end:
            if current_hour >= quiet_start or current_hour < quiet_end:
                # Only send critical notifications during quiet hours
                return notification_type in ["offline", "temperature_alert", "ph_alert"]
        else:
            if quiet_start <= current_hour < quiet_end:
                # Only send critical notifications during quiet hours
                return notification_type in ["offline", "temperature_alert", "ph_alert"]
    
    return True

async def send_notification_to_all(
    title: str,
    body: str,
    **kwargs
) -> Dict[str, int]:
    """
    Send a push notification to all subscriptions.
    
    Returns:
        Dict with success and failure counts
    """
    db = next(get_db())
    try:
        subscriptions = db.query(PushSubscription).all()
        
        success_count = 0
        failure_count = 0
        
        for subscription in subscriptions:
            # Check if notification should be sent based on preferences
            notification_type = kwargs.get("data", {}).get("type")
            if notification_type and not await should_send_notification(subscription, notification_type):
                continue
                
            result = await send_push_notification(subscription, title, body, **kwargs)
            if result:
                success_count += 1
            else:
                failure_count += 1
        
        return {
            "total": len(subscriptions),
            "success": success_count,
            "failure": failure_count
        }
    finally:
        db.close()

async def send_tank_notification(
    tank_id: str,
    title: str,
    body: str,
    notification_type: str,
    **kwargs
) -> Dict[str, int]:
    """
    Send a notification about a specific tank.
    
    Args:
        tank_id: ID of the tank
        title: Notification title
        body: Notification body
        notification_type: Type of notification (e.g., "offline", "temperature_alert")
        
    Returns:
        Dict with success and failure counts
    """
    # Add tank ID and notification type to data
    data = kwargs.get("data", {})
    data.update({
        "tank_id": tank_id,
        "type": notification_type
    })
    kwargs["data"] = data
    
    # Add default URL if not provided
    if "url" not in kwargs:
        kwargs["url"] = f"/tanks/{tank_id}"
    
    return await send_notification_to_all(title, body, **kwargs) 