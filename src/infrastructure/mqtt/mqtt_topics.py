"""
MQTT topic definitions and utilities for TankCtl.

Topics follow the format: tankctl/{device_id}/{channel}
Channels: command, telemetry, reported, heartbeat
"""

from enum import Enum


class TopicChannel(str, Enum):
    """MQTT topic channels."""

    COMMAND = "command"
    TELEMETRY = "telemetry"
    REPORTED = "reported"
    HEARTBEAT = "heartbeat"


class MQTTTopics:
    """MQTT topic name definitions and utilities."""

    # Topic base pattern
    BASE_PATTERN = "tankctl/{device_id}/{channel}"

    @staticmethod
    def command_topic(device_id: str) -> str:
        """Get command topic for a device."""
        return f"tankctl/{device_id}/command"

    @staticmethod
    def telemetry_topic(device_id: str) -> str:
        """Get telemetry topic for a device."""
        return f"tankctl/{device_id}/telemetry"

    @staticmethod
    def reported_topic(device_id: str) -> str:
        """Get reported state topic for a device."""
        return f"tankctl/{device_id}/reported"

    @staticmethod
    def heartbeat_topic(device_id: str) -> str:
        """Get heartbeat topic for a device."""
        return f"tankctl/{device_id}/heartbeat"

    # Wildcard subscriptions for backend
    SUBSCRIBE_TELEMETRY = "tankctl/+/telemetry"
    SUBSCRIBE_REPORTED = "tankctl/+/reported"
    SUBSCRIBE_HEARTBEAT = "tankctl/+/heartbeat"

    @staticmethod
    def extract_device_id(topic: str) -> str | None:
        """
        Extract device_id from MQTT topic.

        Example:
            tankctl/tank1/telemetry -> tank1
            tankctl/greenhouse-light-1/command -> greenhouse-light-1

        Args:
            topic: MQTT topic string

        Returns:
            device_id or None if topic doesn't match pattern
        """
        parts = topic.split("/")
        if len(parts) >= 3 and parts[0] == "tankctl":
            return parts[1]
        return None

    @staticmethod
    def extract_channel(topic: str) -> str | None:
        """
        Extract channel from MQTT topic.

        Example:
            tankctl/tank1/telemetry -> telemetry
            tankctl/tank1/command -> command

        Args:
            topic: MQTT topic string

        Returns:
            channel (command, telemetry, reported, heartbeat) or None
        """
        parts = topic.split("/")
        if len(parts) >= 3 and parts[0] == "tankctl":
            return parts[2]
        return None
