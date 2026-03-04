# TASK.md

## Objective

Implement the first working version of the **TankCtl backend**.

The system controls IoT devices (Arduino UNO R4 WiFi) using MQTT and monitors temperature telemetry.

Devices should support:

* light control
* scheduled automation
* telemetry reporting
* device heartbeat monitoring

Temperature telemetry should be visualized in Grafana.

---

# Architecture Rules

Follow the architecture defined in:

docs/ARCHITECTURE.md
docs/DEVICES.md
docs/MQTT_TOPICS.md
docs/COMMANDS.md
docs/EVENTS.md
docs/DEPLOYMENT.md

The backend must follow **clean layered architecture**:

API → Services → Domain → Repository → Infrastructure

Rules:

* API must not directly use MQTT
* API must not access the database
* Business logic belongs in Services
* MQTT handling belongs in Infrastructure
* Database logic belongs in Repositories

---

# Messaging

Devices communicate using MQTT.

Topic format:

tankctl/{device_id}/{channel}

Channels:

command
reported
telemetry
heartbeat

Backend must subscribe to:

tankctl/+/reported
tankctl/+/telemetry
tankctl/+/heartbeat

Commands must be published to:

tankctl/{device_id}/command

Command format:

{
"version": 8,
"command": "set_light",
"value": "on"
}

Commands must be idempotent.

---

# Device Shadow Model

Each device maintains a shadow.

Example:

{
"device_id": "tank1",
"desired": { "light": "on" },
"reported": { "light": "off" },
"version": 8
}

If desired != reported:

the backend must publish a command to reconcile the device.

---

# Features to Implement

Version 1 must support:

* device registry
* device heartbeat tracking
* device shadow
* command publishing
* telemetry ingestion
* scheduled light automation

---

# Required Modules

Implement these modules.

---

## infrastructure/mqtt

mqtt_client.py
mqtt_topics.py

Responsibilities:

* connect to Mosquitto
* subscribe to topics
* route incoming messages
* publish commands

---

## domain

device_shadow.py

Represents desired and reported state.

---

## repositories

device_repository.py
device_shadow_repository.py
telemetry_repository.py

Handles database persistence.

---

## services

device_service.py
shadow_service.py
command_service.py
telemetry_service.py

Responsibilities:

* device lifecycle
* shadow reconciliation
* command publishing
* telemetry storage

---

## API

Use FastAPI.

Create:

api/main.py
api/routes/devices.py
api/routes/commands.py

Endpoints:

GET /devices
GET /devices/{device_id}/shadow
POST /devices/{device_id}/light

---

## Scheduler

Use APScheduler.

Create:

infrastructure/scheduler/scheduler.py

Tasks:

shadow reconciliation (10 seconds)
offline detection (30 seconds)

---

# Telemetry Pipeline

Telemetry flow:

device → MQTT → backend → TimescaleDB → Grafana

Telemetry topic:

tankctl/{device_id}/telemetry

Payload example:

{
"temperature": 24.5
}

---

# Deployment

The system must run using Docker Compose.

Services:

mosquitto
postgres
timescaledb
grafana
tankctl-backend

See docs/DEPLOYMENT.md.

---

# Development Guidelines

Use:

* Python 3.11+
* FastAPI
* pydantic models
* structured logging
* type hints

Keep modules small and readable.

---

# Implementation Order

Implement modules in this order:

1. MQTT infrastructure
2. Device shadow domain model
3. Command service
4. Telemetry service
5. Device service
6. Scheduler
7. FastAPI routes
8. Docker deployment

Do not generate everything at once.

Generate **one module at a time**.
 