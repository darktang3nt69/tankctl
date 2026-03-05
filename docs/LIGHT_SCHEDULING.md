# LIGHT_SCHEDULING.md

## Overview

This document defines the **light scheduling system for TankCtl** using a **Desired State Scheduling Model integrated with Device Shadow**.

Instead of sending commands directly at schedule time, the scheduler updates the **desired state in the device shadow**. The shadow reconciliation mechanism then ensures the device converges to the desired state.

This approach provides:

* reliable automation
* idempotent behavior
* correct recovery after device reconnect
* clean integration with manual overrides

---

# Design Principles

Light control in TankCtl is based on **device shadow state**.

Device shadow example:

```json
{
  "device_id": "tank1",
  "desired": {
    "light": "on"
  },
  "reported": {
    "light": "off"
  },
  "version": 12
}
```

The scheduler modifies **desired.light** instead of publishing commands.

If:

```text
desired.light != reported.light
```

the shadow reconciliation system triggers the appropriate command.

---

# Scheduling Model

Each device has **one daily light window**.

Example:

```text
ON  → 18:00
OFF → 06:00
```

Meaning:

```text
18:00 → lights ON
06:00 → lights OFF
```

Lights remain ON during the defined window.

---

# Schedule Data Model

Table: `light_schedules`

```sql
CREATE TABLE light_schedules (
    device_id TEXT PRIMARY KEY,
    on_time TIME NOT NULL,
    off_time TIME NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

Fields:

| Field      | Description                     |
| ---------- | ------------------------------- |
| device_id  | device associated with schedule |
| on_time    | daily light start time          |
| off_time   | daily light stop time           |
| enabled    | schedule active                 |
| created_at | schedule creation time          |

Each device supports **one schedule window**.

---

# API Endpoint

Single endpoint manages both ON and OFF schedule.

## Create / Update Schedule

```text
POST /devices/{device_id}/schedule
```

Request:

```json
{
  "on_time": "18:00",
  "off_time": "06:00"
}
```

Behavior:

1. save schedule in database
2. register scheduler jobs
3. scheduler updates shadow at correct times

---

# Scheduler Behavior

Scheduler runs using **APScheduler**.

Two jobs are created per device.

Example:

```text
18:00 → desired.light = on
06:00 → desired.light = off
```

Scheduler triggers:

```python
shadow_service.set_desired(device_id, {"light": "on"})
```

or

```python
shadow_service.set_desired(device_id, {"light": "off"})
```

---

# Manual Override

Users may manually change light state.

Example:

```text
POST /devices/{device_id}/light
```

Request:

```json
{
  "state": "off"
}
```

This updates the shadow:

```json
{
  "desired": {
    "light": "off"
  }
}
```

Manual overrides **do not modify the schedule**.

---

# Override Behavior

Manual overrides remain active **until the next schedule window**.

Example timeline:

```text
17:30 manual OFF
18:00 schedule ON
```

Result:

```text
18:00 scheduler sets desired.light=on
device turns ON
```

Manual override is automatically replaced by the scheduled state.

---

# Scheduler Logic

When scheduler fires:

1. read schedule
2. compute desired state
3. update device shadow

Example:

```python
def apply_schedule(device_id, state):
    shadow_service.set_desired(device_id, {"light": state})
```

Shadow reconciliation then sends command if needed.

---

# Reconnect Behavior

If a device reconnects:

1. backend reads shadow state
2. reconciliation ensures device matches desired state

Example:

```text
device reconnects at 19:00
desired.light = on
device will turn ON
```

Schedules remain consistent.

---

# Edge Case Handling

### Device Offline

Scheduler still updates desired state.

Device will converge when reconnecting.

---

### Missed Schedule

If backend restarts:

1. scheduler reloads schedules
2. desired state recalculated

---

# Example Daily Timeline

```text
06:00 lights OFF
12:00 manual ON
18:00 schedule ON
22:00 manual OFF
06:00 next day schedule OFF
```

Manual overrides only last until next schedule event.

---

# Integration with Device Shadow

Scheduler interacts only with:

```text
shadow_service
```

It never publishes commands directly.

Flow:

```text
Scheduler
   ↓
Shadow Service
   ↓
Command Service
   ↓
MQTT
   ↓
Device
```

---

# Advantages of Desired-State Scheduling

Compared to command-based scheduling:

| Feature                   | Command Scheduling | Desired-State Scheduling |
| ------------------------- | ------------------ | ------------------------ |
| device reconnect recovery | poor               | excellent                |
| idempotent automation     | weak               | strong                   |
| manual override support   | complex            | simple                   |
| system reliability        | medium             | high                     |

---

# Future Improvements

Potential enhancements:

* sunrise/sunset automation
* seasonal schedules
* light intensity ramps
* device group schedules
* holiday exceptions

---

# Design Goals

The light scheduling system is designed to be:

* deterministic
* resilient to restarts
* integrated with device shadow
* compatible with manual overrides
* simple to operate
