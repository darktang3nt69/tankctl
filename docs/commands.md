# COMMANDS.md

## Overview

This document defines all **commands that the TankCtl backend can send to devices**.

Commands are delivered via **MQTT** and executed by the device firmware.

All commands must be:

* deterministic
* idempotent
* versioned

Commands are sent on the device command topic:

```text
tankctl/{device_id}/command
```

---

# Command Format

Every command message must follow this structure:

```json
{
  "version": 8,
  "command": "set_light",
  "value": "on"
}
```

Field definitions:

| Field   | Description                                 |
| ------- | ------------------------------------------- |
| version | command version number used for idempotency |
| command | command name                                |
| value   | command parameter                           |

---

# Idempotency Rules

Devices must track the last processed command version.

Command execution logic:

```text
if version <= last_processed_version:
    ignore command
else:
    execute command
```

This prevents duplicate execution when messages are retried.

---

# Command Transport

Commands are delivered using MQTT.

Topic:

```text
tankctl/{device_id}/command
```

Example:

```text
tankctl/tank1/command
```

QoS recommendation:

```text
QoS 1
```

Commands must **not be retained**.

---

# Supported Commands

## set_light

Controls a light connected to the device.

Payload:

```json
{
  "version": 5,
  "command": "set_light",
  "value": "on"
}
```

Possible values:

```text
on
off
```

Device behavior:

```text
on  → turn light relay ON
off → turn light relay OFF
```

After execution the device must publish reported state.

Example reported message:

```json
{
  "light": "on"
}
```

---

## reboot_device

Reboots the device.

Payload:

```json
{
  "version": 6,
  "command": "reboot_device"
}
```

Device behavior:

1. publish reported state
2. reboot device

---

## request_status

Requests immediate status update.

Payload:

```json
{
  "version": 9,
  "command": "request_status"
}
```

Device behavior:

Device publishes:

```text
tankctl/{device_id}/reported
tankctl/{device_id}/telemetry
```

---

# Scheduled Commands

The backend scheduler can generate commands automatically.

Example automation:

```text
18:00 → set_light on
06:00 → set_light off
```

These scheduled commands use the same MQTT command format.

---

# Command Execution Flow

Example flow for turning a light on:

```text
User creates schedule
        ↓
Scheduler triggers command
        ↓
Backend publishes command
        ↓
tankctl/tank1/command
        ↓
Device receives command
        ↓
Device executes action
        ↓
Device publishes reported state
        ↓
tankctl/tank1/reported
```

---

# Error Handling

If a command cannot be executed, the device should publish an error message.

Example:

```json
{
  "error": "unknown_command",
  "command": "invalid_command"
}
```

Topic:

```text
tankctl/{device_id}/reported
```

---

# Future Commands

Future extensions may include:

```text
set_config
update_firmware
set_threshold
toggle_pump
```

These commands are not part of the initial implementation.

---

# Design Goals

The TankCtl command system is designed to be:

* simple for microcontrollers
* reliable under network retries
* easy to extend
* consistent with MQTT messaging
