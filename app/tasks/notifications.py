"""
Notification tasks for TankCTL.

This module contains Celery tasks for sending notifications via Discord.
"""

import httpx
from celery import shared_task
from app.core.config import settings

@shared_task(queue="notifications")
def send_discord_notification(message: str) -> None:
    """
    Send a notification to Discord via webhook.
    
    Args:
        message: The message to send
    """
    if not settings.DISCORD_ENABLED or not settings.DISCORD_WEBHOOK_URL:
        return
    
    try:
        payload = {
            "content": message,
            "username": "TankCTL",
            "avatar_url": "https://raw.githubusercontent.com/yourusername/tankctl/main/assets/logo.png"
        }
        
        with httpx.Client() as client:
            response = client.post(
                settings.DISCORD_WEBHOOK_URL,
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()
            
    except Exception as e:
        # Log the error but don't retry - we don't want to spam notifications
        print(f"Failed to send Discord notification: {e}")

@shared_task(queue="notifications")
def check_tank_health() -> None:
    """
    Check tank health and send notifications for offline tanks.
    """
    from datetime import datetime, timedelta
    from sqlalchemy.orm import Session
    from app.db.session import get_db
    from app.db.models import Tank, EventLog
    
    db: Session = next(get_db())
    try:
        # Find tanks that haven't been seen in over 60 seconds
        offline_threshold = datetime.utcnow() - timedelta(seconds=60)
        offline_tanks = db.query(Tank).filter(
            Tank.last_seen < offline_threshold,
            Tank.is_active == True
        ).all()
        
        for tank in offline_tanks:
            # Log the event
            event = EventLog(
                tank_id=tank.id,
                event_type="tank_offline",
                details={
                    "last_seen": tank.last_seen.isoformat(),
                    "threshold": offline_threshold.isoformat()
                }
            )
            db.add(event)
            
            # Send notification
            send_discord_notification.delay(
                f"🚨 Tank {tank.name} (ID: {tank.id}) is offline! "
                f"Last seen: {tank.last_seen.isoformat()}"
            )
        
        db.commit()
        
    finally:
        db.close() 