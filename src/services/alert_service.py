"""Alert service that evaluates events and dispatches notifications."""

import time
from datetime import datetime, timezone

from src.config.settings import settings
from src.domain.event import Event
from src.services.push_notification_service import PushNotificationService
from src.repository.device_push_token_repository import DevicePushTokenRepository
from src.infrastructure.db.database import db
from src.utils.logger import get_logger
from src.utils.datetime_utils import isoformat_in_app_timezone

logger = get_logger(__name__)


class AlertService:
    """Evaluates alert rules and sends rate-limited notifications via FCM."""

    def __init__(self):
        # Use a DB session for token repository
        session = db.get_session()
        token_repo = DevicePushTokenRepository(session)
        self.push_service = PushNotificationService(
            token_repo,
            settings.fcm_service_account_json,
            settings.fcm_project_id,
        )
        self._last_sent_by_key: dict[str, float] = {}

    def _can_send(self, alert_key: str) -> bool:
        """Return True if enough time elapsed since last alert for this key."""
        now = time.time()
        last_sent = self._last_sent_by_key.get(alert_key)
        if last_sent is None:
            return True
        return (now - last_sent) >= settings.alerts.min_interval_seconds

    def _mark_sent(self, alert_key: str) -> None:
        self._last_sent_by_key[alert_key] = time.time()

    def _send_rate_limited(self, alert_key: str, device_id: str, title: str, message: str, notification_type: str = "info") -> None:
        """Send FCM push if not suppressed by per-key cooldown."""
        if not settings.alerts.enabled:
            logger.debug("alerts_disabled_skip", alert_key=alert_key)
            return

        if not self._can_send(alert_key):
            logger.debug("alert_suppressed_rate_limit", alert_key=alert_key)
            return

        sent = self.push_service.broadcast_fcm(device_id, title, message, notification_type=notification_type)
        if sent > 0:
            self._mark_sent(alert_key)
            logger.info("alert_sent", alert_key=alert_key, sent=sent, type=notification_type)

    def _get_timestamp(self) -> str:
        """Get formatted timestamp in app timezone."""
        now_utc = datetime.now(timezone.utc)
        iso_str = isoformat_in_app_timezone(now_utc)
        # Extract just the time part (HH:MM:SS)
        return iso_str.split("T")[1].split("+")[0]

    def handle_device_offline_event(self, event: Event) -> None:
        """Handle device_offline event."""
        device_id = event.device_id or "unknown"
        alert_key = f"offline:{device_id}"
        timestamp = self._get_timestamp()
        title = f"🚨 {device_id} is Offline"
        message = f"{device_id} stopped responding at {timestamp}.\nCheck power and network connectivity."
        self._send_rate_limited(alert_key, device_id, title, message, "device_offline")

    def handle_device_online_event(self, event: Event) -> None:
        """Handle device_online recovery event."""
        device_id = event.device_id or "unknown"
        alert_key = f"online:{device_id}"
        timestamp = self._get_timestamp()
        title = f"✅ {device_id} is Back Online"
        message = f"{device_id} reconnected and is operating normally at {timestamp}."
        self._send_rate_limited(alert_key, device_id, title, message, "device_online")

    def handle_light_state_change_event(self, event: Event) -> None:
        """Handle light state change based on reported state (not reconciliation)."""
        if event.metadata.get("_from_reconciliation") is True:
            return

        device_id = event.device_id or "unknown"
        light_state = event.metadata.get("light") if event.metadata else None
        if light_state is None:
            return

        alert_key = f"light_state:{device_id}"
        timestamp = self._get_timestamp()
        state_text = "ON" if light_state.lower() == "on" else "OFF"
        emoji = "💡" if light_state.lower() == "on" else "🌙"
        title = f"{emoji} Lights {state_text} — {device_id}"
        message = f"Aquarium lights on {device_id} turned {state_text.lower()} at {timestamp}."
        notification_type = "light_on" if light_state.lower() == "on" else "light_off"
        self._send_rate_limited(alert_key, device_id, title, message, notification_type)

    def handle_telemetry_event(self, event: Event) -> None:
        """Handle telemetry_received event for temperature threshold alerts."""
        device_id = event.device_id or "unknown"
        temperature = event.metadata.get("temperature") if event.metadata else None
        if temperature is None:
            return

        try:
            temp_c = float(temperature)
        except (TypeError, ValueError):
            logger.warning("temperature_alert_invalid_value", device_id=device_id, value=str(temperature))
            return

        timestamp = self._get_timestamp()
        
        # Handle HIGH temperature alert
        high_alert_key = f"temp_high:{device_id}"
        if temp_c > settings.alerts.temperature_high_c:
            # Temperature is high — send alert if cooldown elapsed
            temp_diff = temp_c - settings.alerts.temperature_high_c
            title = f"🔥 High Temp Alert — {device_id}"
            message = f"Water temperature is {temp_c:.1f}°C — {temp_diff:.1f}°C above the {settings.alerts.temperature_high_c}°C limit.\nCheck your cooling system immediately. Detected at {timestamp}."
            self._send_rate_limited(high_alert_key, device_id, title, message, "temperature_high")
        else:
            # Temperature returned to normal — clear cooldown so next alert sends immediately
            if high_alert_key in self._last_sent_by_key:
                del self._last_sent_by_key[high_alert_key]
                logger.info("temperature_high_resolved", device_id=device_id, reading=temp_c)
        
        # Handle LOW temperature alert
        low_alert_key = f"temp_low:{device_id}"
        if temp_c < settings.alerts.temperature_low_c:
            # Temperature is low — send alert if cooldown elapsed
            temp_diff = settings.alerts.temperature_low_c - temp_c
            title = f"❄️ Low Temp Alert — {device_id}"
            message = f"Water temperature is {temp_c:.1f}°C — {temp_diff:.1f}°C below the {settings.alerts.temperature_low_c}°C limit.\nCheck your heating system immediately. Detected at {timestamp}."
            self._send_rate_limited(low_alert_key, device_id, title, message, "temperature_low")
        else:
            # Temperature returned to normal — clear cooldown so next alert sends immediately
            if low_alert_key in self._last_sent_by_key:
                del self._last_sent_by_key[low_alert_key]
                logger.info("temperature_low_resolved", device_id=device_id, reading=temp_c)
