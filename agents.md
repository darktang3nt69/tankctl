# AGENTS.md

## Project

**TankCtrl**

TankCtrl is a self-hosted IoT controller for managing water tank devices built with:

* Python backend
* MQTT (Mosquitto broker)
* Arduino UNO R4 WiFi devices
* Device Shadow state model

The backend manages device state, commands, and telemetry while devices execute actions and report their status.

---

# Architecture Overview

TankCtrl follows a **Layered Architecture**.

```
API → Services → Domain → Repository → Infrastructure
```

### Rules

* API must never talk directly to MQTT or the database
* Business logic belongs in the **service layer**
* Domain models must remain **pure and framework-agnostic**
* Infrastructure handles external systems (MQTT, DB, scheduler)

---

# Project Structure

```
tankctl/
│
├── api/
│   ├── routes/
│   │   ├── device_routes.py
│   │   └── health_routes.py
│   └── schemas.py
│
├── domain/
│   ├── device.py
│   ├── device_shadow.py
│   └── command.py
│
├── services/
│   ├── device_service.py
│   ├── shadow_service.py
│   └── command_service.py
│
├── repository/
│   ├── device_repository.py
│   └── shadow_repository.py
│
├── infrastructure/
│   ├── mqtt/
│   │   ├── mqtt_client.py
│   │   └── mqtt_topics.py
│   │
│   ├── db/
│   │   └── database.py
│   │
│   └── scheduler/
│       └── scheduler.py
│
├── device/
│   └── shadow_reconciler.py
│
├── config/
│   └── settings.py
│
├── utils/
│   └── logger.py
│
├── main.py
└── AGENTS.md
```

---

# Key Concepts

## Device Shadow

Each device has a shadow state.

```
DeviceShadow
 ├─ desired
 ├─ reported
 └─ version
```

Example:

```json
{
  "device_id": "tank1",
  "version": 4,
  "desired": { "pump": "on" },
  "reported": { "pump": "off" }
}
```

The backend reconciles differences between `desired` and `reported`.

---

# MQTT Topics

```
tankctl/{device_id}/telemetry
tankctl/{device_id}/reported
tankctl/{device_id}/command
tankctl/{device_id}/status
```

### Example

```
tankctl/tank1/telemetry
tankctl/tank1/command
```

---

# Command Format

Commands must include a version.

```json
{
  "command": "set_pump",
  "value": "on",
  "version": 7
}
```

Devices must ignore commands with older versions.

---

# Scheduler

APScheduler runs periodic tasks:

```
shadow reconciliation
device heartbeat monitoring
retry failed commands
telemetry cleanup
```

Example reconciliation rule:

```
if desired != reported:
    publish command
```

---

# Coding Guidelines

### Python

* Use type hints
* Prefer dataclasses or pydantic models
* Avoid global state

### Architecture

Never allow:

```
API → MQTT
API → DB
```

Always follow:

```
API → Service → Repository / Infrastructure
```

---

# Logging

Use structured logging.

Example log event:

```
device_id=abc123 event=command_sent command=set_pump
```

---

# Device Firmware Expectations

Devices must:

Subscribe to:

```
tankctl/{device_id}/command
```

Publish to:

```
tankctl/{device_id}/telemetry
tankctl/{device_id}/reported
tankctl/{device_id}/status
```

Devices should implement idempotency using command version numbers.

---

# Design Patterns Used

* Publish–Subscribe
* Device Shadow
* Command Pattern
* Layered Architecture
* Repository Pattern
* Scheduler Pattern

---

# Development Workflow

1. Implement domain models
2. Implement services
3. Implement repositories
4. Implement infrastructure adapters
5. Implement API routes

Never skip layers.

---

# Goals

TankCtrl should remain:

* Simple
* Self-hosted
* MQTT-first
* Device-centric
* Reliable even when devices disconnect

---

# Non-Goals

TankCtrl is **not** intended to be:

* a full cloud IoT platform
* a distributed microservice system
* a vendor-locked system

It should remain a lightweight device controller.
