"""
Event domain model for TankCtl.

Events represent important state changes in the system.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, Literal
import time


EventType = Literal[
    # Device lifecycle
    "device_registered",
    "device_online",
    "device_offline",
    
    # Command lifecycle
    "command_sent",
    "command_executed",
    "command_failed",
    
    # Shadow lifecycle
    "shadow_synchronized",
    "shadow_drifted",
    
    # Telemetry
    "telemetry_received",
    
    # Device state
    "light_state_changed",
    
    # Scheduler
    "scheduled_command_triggered",
    "shadow_reconciliation_started",
    
    # MQTT
    "mqtt_connected",
    "mqtt_disconnected",

    # Device warnings
    "device_warning",
]


@dataclass
class Event:
    """
    Domain model for system events.
    
    Attributes:
        event: Event type name
        device_id: Associated device (if applicable)
        timestamp: Unix timestamp (seconds)
        metadata: Additional context
    """
    
    event: EventType
    timestamp: float = field(default_factory=time.time)
    device_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return asdict(self)
    
    def __str__(self) -> str:
        """String representation for logging."""
        parts = [f"event={self.event}"]
        if self.device_id:
            parts.append(f"device_id={self.device_id}")
        if self.metadata:
            for key, value in self.metadata.items():
                parts.append(f"{key}={value}")
        return " ".join(parts)


# Event factory functions for common event types

def device_registered_event(device_id: str) -> Event:
    """Device registered event."""
    return Event(
        event="device_registered",
        device_id=device_id,
    )


def device_online_event(device_id: str) -> Event:
    """Device came online event."""
    return Event(
        event="device_online",
        device_id=device_id,
    )


def device_offline_event(device_id: str) -> Event:
    """Device went offline event."""
    return Event(
        event="device_offline",
        device_id=device_id,
    )


def command_sent_event(device_id: str, command: str, value: Optional[str] = None, version: Optional[int] = None) -> Event:
    """Command sent event."""
    metadata = {"command": command}
    if value is not None:
        metadata["value"] = value
    if version is not None:
        metadata["version"] = version
    
    return Event(
        event="command_sent",
        device_id=device_id,
        metadata=metadata,
    )


def command_executed_event(device_id: str, command: str, value: Optional[str] = None) -> Event:
    """Command executed event."""
    metadata = {"command": command}
    if value is not None:
        metadata["value"] = value
    
    return Event(
        event="command_executed",
        device_id=device_id,
        metadata=metadata,
    )


def command_failed_event(device_id: str, command: str, reason: str = "unknown") -> Event:
    """Command failed event."""
    return Event(
        event="command_failed",
        device_id=device_id,
        metadata={"command": command, "reason": reason},
    )


def shadow_synchronized_event(device_id: str, version: int) -> Event:
    """Shadow synchronized event."""
    return Event(
        event="shadow_synchronized",
        device_id=device_id,
        metadata={"version": version},
    )


def shadow_drifted_event(device_id: str, version: int, delta: Dict[str, Any]) -> Event:
    """Shadow drifted event."""
    return Event(
        event="shadow_drifted",
        device_id=device_id,
        metadata={"version": version, "delta": delta},
    )


def telemetry_received_event(device_id: str, metrics: Dict[str, Any]) -> Event:
    """Telemetry received event."""
    return Event(
        event="telemetry_received",
        device_id=device_id,
        metadata=metrics,
    )


def shadow_reconciliation_started_event(device_id: str) -> Event:
    """Shadow reconciliation started event."""
    return Event(
        event="shadow_reconciliation_started",
        device_id=device_id,
    )


def mqtt_connected_event() -> Event:
    """MQTT connected event."""
    return Event(event="mqtt_connected")


def mqtt_disconnected_event() -> Event:
    """MQTT disconnected event."""
    return Event(event="mqtt_disconnected")
