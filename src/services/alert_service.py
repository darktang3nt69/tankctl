"""Alert service that evaluates events and dispatches notifications."""

import time
from datetime import datetime, timezone

from src.config.settings import settings
from src.domain.event import Event
from src.services.notification_service import NotificationService
from src.utils.logger import get_logger
from src.utils.datetime_utils import isoformat_in_app_timezone

logger = get_logger(__name__)


class AlertService:
    """Evaluates alert rules and sends rate-limited notifications."""

    def __init__(self):
        self.notification_service = NotificationService()
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

    def _send_rate_limited(self, alert_key: str, message: str) -> None:
        """Send alert message if not suppressed by per-key cooldown."""
        if not settings.alerts.enabled:
            logger.debug("alerts_disabled_skip", alert_key=alert_key)
            return

        if not self._can_send(alert_key):
            logger.debug("alert_suppressed_rate_limit", alert_key=alert_key)
            return

        sent = self.notification_service.send_whatsapp(message)
        if sent:
            self._mark_sent(alert_key)
            logger.info("alert_sent", alert_key=alert_key)

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
        message = f"""🚨 DEVICE OFFLINE 🚨

📍 Device: {device_id}
❌ Status: DISCONNECTED
⏰ Time: {timestamp}

Check: Power & Network"""
        self._send_rate_limited(alert_key, message)

    def handle_device_online_event(self, event: Event) -> None:
        """Handle device_online recovery event."""
        device_id = event.device_id or "unknown"
        alert_key = f"online:{device_id}"
        timestamp = self._get_timestamp()
        message = f"""✅ DEVICE RECOVERED ✅

📍 Device: {device_id}
🟢 Status: ONLINE
⏰ Time: {timestamp}

System resumed normal operation"""
        self._send_rate_limited(alert_key, message)

    def handle_light_state_change_event(self, event: Event) -> None:
        """Handle light state change based on reported state (not reconciliation)."""
        # Skip if this is from shadow reconciliation
        if event.metadata.get("_from_reconciliation") is True:
            return

        device_id = event.device_id or "unknown"
        light_state = event.metadata.get("light") if event.metadata else None
        if light_state is None:
            return

        alert_key = f"light_state:{device_id}"
        timestamp = self._get_timestamp()
        state_text = "ON" if light_state.lower() == "on" else "OFF"
        message = f"""💡 LIGHT {state_text} 💡

📍 Device: {device_id}
💡 State: {state_text}
⏰ Time: {timestamp}"""
        self._send_rate_limited(alert_key, message)

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
        if temp_c > settings.alerts.temperature_high_c:
            alert_key = f"temp_high:{device_id}"
            temp_diff = temp_c - settings.alerts.temperature_high_c
            message = f"""🔥 TEMPERATURE HIGH 🔥

📍 Device: {device_id}
🌡️  Reading: {temp_c:.1f}°C (⬆️ +{temp_diff:.1f}°C)
⚠️  Threshold: >{settings.alerts.temperature_high_c}°C
⏰ Time: {timestamp}

Action: Check cooling system"""
            self._send_rate_limited(alert_key, message)
        elif temp_c < settings.alerts.temperature_low_c:
            alert_key = f"temp_low:{device_id}"
            temp_diff = settings.alerts.temperature_low_c - temp_c
            message = f"""❄️ TEMPERATURE LOW ❄️

📍 Device: {device_id}
🌡️  Reading: {temp_c:.1f}°C (⬇️ -{temp_diff:.1f}°C)
⚠️  Threshold: <{settings.alerts.temperature_low_c}°C
⏰ Time: {timestamp}

Action: Check heating system"""
            self._send_rate_limited(alert_key, message)
