"""
Discord notification module for TankCTL.

This module provides functionality to send notifications to Discord channels
via webhooks. It handles various types of alerts and notifications for the
aquarium control system.

Best Practices:
- Use async/await for network calls
- Implement proper error handling
- Use type hints
- Add comprehensive logging
- Support retry mechanisms
- Validate webhook URLs
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import aiohttp
from app.core.config import settings
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class DiscordNotifier:
    """
    Discord notification handler.
    
    This class manages sending notifications to Discord channels via webhooks.
    It supports different types of alerts and includes retry mechanisms.
    """
    
    def __init__(self, webhook_url: str, retry_count: int = 3, retry_delay: int = 5):
        """
        Initialize the Discord notifier.
        
        Args:
            webhook_url: Discord webhook URL
            retry_count: Number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.webhook_url = webhook_url
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Create aiohttp session when entering context."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session when exiting context."""
        if self.session:
            await self.session.close()
    
    async def _send_webhook(self, payload: Dict[str, Any]) -> bool:
        """
        Send a webhook request to Discord with retry logic.
        
        Args:
            payload: Webhook payload
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        for attempt in range(self.retry_count):
            try:
                async with self.session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10
                ) as response:
                    if response.status == 204:
                        return True
                    logger.error(
                        f"Discord webhook failed (attempt {attempt + 1}/{self.retry_count}): "
                        f"HTTP {response.status}"
                    )
            except Exception as e:
                logger.error(
                    f"Discord webhook error (attempt {attempt + 1}/{self.retry_count}): {str(e)}"
                )
            
            if attempt < self.retry_count - 1:
                await asyncio.sleep(self.retry_delay)
        
        return False
    
    async def send_alert(
        self,
        title: str,
        description: str,
        color: int = 0xFF0000,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send a generic alert to Discord.
        
        Args:
            title: Alert title
            description: Alert description
            color: Embed color (hex)
            timestamp: Optional timestamp
            
        Returns:
            bool: True if successful, False otherwise
        """
        payload = {
            "embeds": [{
                "title": title,
                "description": description,
                "color": color,
                "timestamp": timestamp.isoformat() if timestamp else None
            }]
        }
        
        return await self._send_webhook(payload)
    
    async def command_failure(
        self,
        tank_name: str,
        command: str,
        error: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send a command failure alert.
        
        Args:
            tank_name: Name of the tank
            command: Failed command
            error: Error message
            timestamp: Optional timestamp
            
        Returns:
            bool: True if successful, False otherwise
        """
        return await self.send_alert(
            title="Command Failed",
            description=(
                f"**Tank:** {tank_name}\n"
                f"**Command:** {command}\n"
                f"**Error:** {error}"
            ),
            color=0xFF0000,  # Red
            timestamp=timestamp
        )
    
    async def tank_offline(
        self,
        tank_name: str,
        last_seen: datetime,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send a tank offline alert.
        
        Args:
            tank_name: Name of the tank
            last_seen: Last seen timestamp
            timestamp: Optional timestamp
            
        Returns:
            bool: True if successful, False otherwise
        """
        return await self.send_alert(
            title="Tank Offline",
            description=(
                f"**Tank:** {tank_name}\n"
                f"**Last Seen:** {last_seen.isoformat()}"
            ),
            color=0xFFA500,  # Orange
            timestamp=timestamp
        )
    
    async def command_success(
        self,
        tank_name: str,
        command: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send a command success notification.
        
        Args:
            tank_name: Name of the tank
            command: Executed command
            timestamp: Optional timestamp
            
        Returns:
            bool: True if successful, False otherwise
        """
        return await self.send_alert(
            title="Command Executed",
            description=(
                f"**Tank:** {tank_name}\n"
                f"**Command:** {command}"
            ),
            color=0x00FF00,  # Green
            timestamp=timestamp
        )

# Create a global instance
discord_notifier = DiscordNotifier(settings.DISCORD_WEBHOOK_URL) 