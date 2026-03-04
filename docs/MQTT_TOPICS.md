# MQTT_TOPICS.md

## Overview

This document defines all MQTT topics used by TankCtl.

Topics are the **communication interface between devices and backend services**.

Topic naming must remain **stable across firmware and backend versions**.

---

# Topic Structure

All topics follow this format:

```text
tankctl/{device_id}/{channel}
```

Example:

```text
tankctl/tank1/telemetry
tankctl/tank1/command
tankctl/tank1/reported
tankctl/tank1/heartbeat
```

---

# Topic Categories

## Command

Backend → Device

Topic:

```text
tankctl/{device_id}/command
```

Purpose:

Send commands to a specific device.

Example payload:

```json
{
  "version": 7,
  "command": "set_light",
  "value": "on"
}
```

Devices must subscribe to this topic.

---

## Reported State

Device → Backend

Topic:

```text
tankctl/{device_id}/reported
```

Purpose:

Device reports its actual state after executing commands.

Example payload:

```json
{
  "light": "on"
}
```

---

## Telemetry

Device → Backend

Topic:

```text
tankctl/{device_id}/telemetry
```

Purpose:

Sensor data from devices.

Example payload:

```json
{
  "temperature": 24.5
}
```

Telemetry data is stored in the telemetry database and visualized in Grafana.

---

## Heartbeat

Device → Backend

Topic:

```text
tankctl/{device_id}/heartbeat
```

Purpose:

Indicates device health and connectivity.

Example payload:

```json
{
  "status": "online",
  "uptime": 120
}
```

Recommended interval:

```text
30 seconds
```

---

# Topic Direction

| Topic     | Publisher | Subscriber |
| --------- | --------- | ---------- |
| command   | backend   | device     |
| reported  | device    | backend    |
| telemetry | device    | backend    |
| heartbeat | device    | backend    |

---

# MQTT QoS Levels

Recommended QoS configuration:

```text
command → QoS 1
reported → QoS 1
telemetry → QoS 0
heartbeat → QoS 0
```

Explanation:

Commands and state updates should not be lost.
Telemetry can tolerate occasional packet loss.

---

# Retained Messages

Retained messages should be used carefully.

Recommended usage:

```text
reported state → retained
commands → not retained
telemetry → not retained
heartbeat → not retained
```

This ensures the backend can recover the last known device state.

---

# Topic Examples

Example device:

```text
device_id = tank1
```

Topics:

```text
tankctl/tank1/command
tankctl/tank1/reported
tankctl/tank1/telemetry
tankctl/tank1/heartbeat
```

---

# Backend Topic Subscriptions

Backend MQTT client subscribes to:

```text
tankctl/+/reported
tankctl/+/telemetry
tankctl/+/heartbeat
```

The `+` wildcard allows the backend to receive messages from all devices.

---

# Device Topic Subscriptions

Devices subscribe only to their command topic.

Example:

```text
tankctl/tank1/command
```

This ensures commands are targeted to the correct device.

---

# Future Extensions

Possible future channels:

```text
tankctl/{device_id}/firmware
tankctl/{device_id}/logs
tankctl/{device_id}/config
```

These are not required for the initial version.

---

# Design Goals

The MQTT topic design prioritizes:

* clarity
* stability
* minimal complexity
* easy device implementation
* backend scalability
