"""
Notification tasks for TankCTL.

This module contains Celery tasks for sending notifications via Discord.
"""

import asyncio
from celery import shared_task
from app.core.config import settings
from app.utils.discord import discord_notifier
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Tank, EventLog

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
        # Run the async notification in the event loop
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(
            discord_notifier.send_alert(
                title="TankCTL Notification",
                description=message,
                color=0x00FF00,  # Green for normal notifications
                timestamp=datetime.utcnow()
            )
        )
        
        if not success:
            print("Failed to send Discord notification after retries")
            
    except Exception as e:
        # Log the error but don't retry - we don't want to spam notifications
        print(f"Failed to send Discord notification: {e}")

@shared_task(queue="notifications")
def check_tank_health() -> None:
    """
    Check tank health and send notifications for offline tanks.
    """
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
            
            # Send notification using the async notifier
            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                discord_notifier.tank_offline(
                    tank_name=tank.name,
                    last_seen=tank.last_seen,
                    timestamp=datetime.utcnow()
                )
            )
        
        db.commit()
        
    finally:
        db.close() 