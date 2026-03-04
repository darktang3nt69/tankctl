# EVENTS.md

## Overview

This document defines the **system events used within TankCtl**.

Events represent important state changes or actions occurring in the system.
They are primarily used for:

* logging
* monitoring
* debugging
* observability
* future automation

Events do **not replace MQTT messages**. Instead, they describe **system-level occurrences** derived from device activity or backend operations.

---

# Event Model

Each event should follow a consistent structure.

Example event payload:

```json
{
  "event": "device_online",
  "device_id": "tank1",
  "timestamp": 1710000000,
  "metadata": {}
}
```

Fields:

| Field     | Description                      |
| --------- | -------------------------------- |
| event     | event name                       |
| device_id | device associated with the event |
| timestamp | event time (unix epoch)          |
| metadata  | optional additional data         |

---

# Event Categories

Events fall into several categories:

* device lifecycle
* command lifecycle
* telemetry events
* system events

---

# Device Lifecycle Events

## device_registered

Triggered when a new device is created in the system.

Example:

```json
{
  "event": "device_registered",
  "device_id": "tank1"
}
```

---

## device_online

Triggered when a device connects and sends a heartbeat.

Example:

```json
{
  "event": "device_online",
  "device_id": "tank1"
}
```

---

## device_offline

Triggered when a device has not sent heartbeat for the configured timeout.

Example:

```json
{
  "event": "device_offline",
  "device_id": "tank1"
}
```

Offline detection rule:

```text
now - last_seen > 60 seconds
```

---

# Command Lifecycle Events

## command_sent

Triggered when the backend publishes a command to MQTT.

Example:

```json
{
  "event": "command_sent",
  "device_id": "tank1",
  "metadata": {
    "command": "set_light",
    "value": "on"
  }
}
```

---

## command_executed

Triggered when the device reports successful command execution.

Example:

```json
{
  "event": "command_executed",
  "device_id": "tank1",
  "metadata": {
    "command": "set_light",
    "value": "on"
  }
}
```

---

## command_failed

Triggered if a command cannot be executed.

Example:

```json
{
  "event": "command_failed",
  "device_id": "tank1",
  "metadata": {
    "command": "set_light",
    "reason": "relay_error"
  }
}
```

---

# Telemetry Events

## telemetry_received

Triggered when telemetry data arrives from a device.

Example:

```json
{
  "event": "telemetry_received",
  "device_id": "tank1",
  "metadata": {
    "temperature": 24.6
  }
}
```

Telemetry events are useful for:

* debugging
* system health analysis
* metrics collection

---

# Scheduler Events

## scheduled_command_triggered

Triggered when a scheduled automation fires.

Example:

```json
{
  "event": "scheduled_command_triggered",
  "device_id": "tank1",
  "metadata": {
    "command": "set_light",
    "value": "on"
  }
}
```

---

# System Events

## mqtt_connected

Triggered when the backend connects to the MQTT broker.

Example:

```json
{
  "event": "mqtt_connected"
}
```

---

## mqtt_disconnected

Triggered when MQTT connection is lost.

Example:

```json
{
  "event": "mqtt_disconnected"
}
```

---

# Event Logging

Events should be logged using structured logging.

Example log entry:

```text
timestamp=1710000000 event=device_online device_id=tank1
```

Recommended fields:

```text
timestamp
event
device_id
metadata
```

---

# Event Processing

Events may later be used for:

* alerts
* automation triggers
* analytics
* audit logs

However, the initial version of TankCtl will **only log events**.

---

# Event Flow Example

Example command execution lifecycle:

```text
Scheduler triggers command
        ↓
event: scheduled_command_triggered
        ↓
Backend publishes MQTT command
        ↓
event: command_sent
        ↓
Device executes command
        ↓
Device publishes reported state
        ↓
event: command_executed
```

---

# Design Goals

The TankCtl event system aims to be:

* simple
* observable
* extensible
* compatible with structured logging

Events provide insight into system behavior without complicating the MQTT protocol.
