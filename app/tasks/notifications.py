"""
Notification tasks for TankCTL.

This module contains Celery tasks for sending notifications via Discord.
"""

import asyncio
from celery import Celery
from app.core.config import settings
from app.utils.discord import discord_notifier
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import get_sync_db
from app.db.models import Tank, EventLog, NotificationLog
import os
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Create Celery instance
celery_app = Celery(
    "tankctl",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="notifications",
    time_limit=30,
    soft_time_limit=25,
    acks_late=True,
    reject_on_worker_lost=True
)
def send_discord_notification(self, message: str, tank_id: Optional[int] = None) -> None:
    """Send a notification to Discord."""
    try:
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if not webhook_url:
            logger.error("DISCORD_WEBHOOK_URL not set")
            return

        # Get tank name if tank_id is provided
        tank_name = None
        if tank_id:
            db = next(get_sync_db())
            try:
                tank = db.query(Tank).filter(Tank.id == tank_id).first()
                if tank:
                    tank_name = tank.name
                else:
                    logger.error(f"Tank {tank_id} not found")
            except Exception as e:
                logger.error(f"Error getting tank name: {str(e)}")
            finally:
                db.close()

        # Create notification log
        db = next(get_sync_db())
        try:
            log = NotificationLog()
            log.message = message
            log.tank_id = tank_id
            log.channel = "discord"
            log.status = "pending"
            log.error_message = None
            log.created_at = datetime.utcnow()
            log.updated_at = datetime.utcnow()
            db.add(log)
            db.commit()
            db.refresh(log)
        except Exception as e:
            logger.error(f"Error creating notification log: {str(e)}")
            db.rollback()
            return
        finally:
            db.close()

        # Format message with tank info
        if tank_name and tank_id:
            formatted_message = f"**Tank {tank_name} (ID: {tank_id})**\n{message}"
        elif tank_id:
            formatted_message = f"**Tank ID: {tank_id}**\n{message}"
        else:
            formatted_message = message

        # Send to Discord
        response = httpx.post(
            webhook_url,
            json={"content": formatted_message},
            timeout=10.0
        )
        response.raise_for_status()

        # Update notification log
        db = next(get_sync_db())
        try:
            log.status = "success"
            log.updated_at = datetime.utcnow()
            db.commit()
        except Exception as e:
            logger.error(f"Error updating notification log: {str(e)}")
            db.rollback()
        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Error sending Discord notification: {str(exc)}")
        # Update notification log
        db = next(get_sync_db())
        try:
            log.status = "failed"
            log.error_message = str(exc)
            log.updated_at = datetime.utcnow()
            db.commit()
        except Exception as e:
            logger.error(f"Error updating notification log: {str(e)}")
            db.rollback()
        finally:
            db.close()
        self.retry(exc=exc)

@celery_app.task(queue="notifications")
def check_tank_health() -> None:
    """
    Check tank health and send notifications for offline tanks.
    """
    db: Session = next(get_sync_db())
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