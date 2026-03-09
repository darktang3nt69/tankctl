# DEVICES.md

## Overview

This document defines how **devices are identified, registered, authenticated, and managed** in the TankCtl system.

Devices are typically **Arduino UNO R4 WiFi controllers** that communicate with the backend through **MQTT (Mosquitto)**.

The design goal is to provide:

* Stable device identity
* Idempotent reconnect behavior
* Secure authentication
* Direct command targeting

Devices must behave similarly to **Kubernetes nodes**, where restarting or reconnecting does **not create a new device**.

---

# Device Identity

Each device has a **stable identity** represented by `device_id`.

Example:

```text
tank1
tank2
greenhouse-light-1
```

This identifier must never change during the device lifetime.

Devices use the `device_id` in:

* MQTT topics
* authentication credentials
* database records

---

# Device Database Model

The backend maintains a **device registry**.

Table structure:

```text
devices
-------
device_id (PRIMARY KEY)
device_secret
status
firmware_version
created_at
last_seen
```

Field definitions:

| Field            | Description                                  |
| ---------------- | -------------------------------------------- |
| device_id        | unique identifier for the device             |
| device_secret    | authentication secret used during MQTT login |
| status           | online/offline                               |
| firmware_version | current firmware version                     |
| last_seen        | last heartbeat timestamp                     |

---

# Device Provisioning

Devices must be **registered before connecting**.

Provisioning flow:

```text
Admin registers device
        ↓
Backend generates device_secret
        ↓
Secret stored in database
        ↓
Secret flashed into device firmware
```

Example API response:

```json
{
  "device_id": "tank1",
  "device_secret": "8fa93d72c6c5a91d"
}
```

The `device_secret` must be stored securely on the device.

---

# MQTT Identity

Devices authenticate with the MQTT broker using:

| Field     | Example              |
| --------- | -------------------- |
| client_id | tankctl-device-tank1 |
| username  | tank1                |
| password  | device_secret        |

Example connection:

```text
client_id = tankctl-device-tank1
username  = tank1
password  = 8fa93d72c6c5a91d
```

This allows the broker to verify device identity.

---

# MQTT Topics

Each device communicates using topics derived from `device_id`.

Format:

```text
tankctl/{device_id}/{channel}
```

Example topics:

```text
tankctl/tank1/command
tankctl/tank1/reported
tankctl/tank1/telemetry
tankctl/tank1/heartbeat
```

---

# Device Boot Sequence

When a device starts:

1. Connect to WiFi
2. Connect to MQTT broker
3. Subscribe to command topic
4. Send heartbeat message

Example subscription:

```text
tankctl/{device_id}/command
```

Example heartbeat message:

```json
{
  "device_id": "tank1",
  "status": "online",
  "uptime": 120
}
```

Topic:

```text
tankctl/tank1/heartbeat
```

---

# Device Reconnect Behavior

If a device disconnects and reconnects:

* It reconnects using the **same client_id**
* It uses the **same device_id**
* It uses the **same device_secret**

The backend updates:

```text
last_seen
status = online
```

No new device record is created.

This ensures **idempotent device behavior**.

---

# Device Status Tracking

Device health is monitored using heartbeat messages.

Recommended interval:

```text
every 30 seconds
```

Offline detection rule:

```text
if now - last_seen > 60 seconds
    mark device offline
```

---

# Command Targeting

Commands are sent using device-specific topics.

Example command topic:

```text
tankctl/tank1/command
```

Command message:

```json
{
  "version": 8,
  "command": "set_light",
  "value": "on"
}
```

Only `tank1` receives this command.

---

# Command Idempotency

Commands include a **version number**.

Devices must ignore commands with:

```text
version <= last_processed_version
```

This prevents duplicate command execution.

Example logic:

```text
if version <= last_version
    ignore
else
    execute command
```

---

# Device Telemetry

Devices publish telemetry data periodically.

Topic:

```text
tankctl/{device_id}/telemetry
```

Example telemetry message:

```json
{
  "temperature": 24.7
}
```

Telemetry data is stored in the telemetry database and visualized in Grafana.

---

# Security Model

Minimum security requirements:

* MQTT authentication using username/password
* unique device_secret per device

Future improvements may include:

* TLS encryption
* device certificates
* signed firmware

---

# Design Goals

The TankCtl device system is designed to be:

* stable across reconnects
* easy for microcontrollers
* secure against unauthorized devices
* simple to extend with new sensors

Devices behave as **persistent system nodes**, not ephemeral clients.
