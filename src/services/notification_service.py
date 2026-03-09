"""Notification service for external alert channels."""

import requests

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Sends notifications to external systems (WhatsApp bot)."""

    def send_whatsapp(self, message: str) -> bool:
        """Send WhatsApp message via local bot API.

        Returns True if message was accepted by the bot API.
        """
        if not settings.whatsapp.enabled:
            logger.debug("whatsapp_disabled_skip")
            return False

        if not settings.whatsapp.phone_number:
            logger.warning("whatsapp_phone_missing")
            return False

        try:
            response = requests.post(
                settings.whatsapp.bot_url,
                json={
                    "number": settings.whatsapp.phone_number,
                    "message": message,
                },
                timeout=settings.whatsapp.request_timeout_seconds,
            )

            if response.status_code >= 400:
                logger.error(
                    "whatsapp_send_failed",
                    status_code=response.status_code,
                    response_text=response.text[:200],
                )
                return False

            logger.info("whatsapp_sent")
            return True

        except Exception as e:
            logger.error("whatsapp_send_error", error=str(e))
            return False
