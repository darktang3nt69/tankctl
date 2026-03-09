# TankCtl Architecture

## Overview

TankCtl is a **self-hosted IoT controller** for managing water tank devices.
It communicates with devices over **MQTT**, stores operational state in **PostgreSQL**, stores telemetry in **TimescaleDB**, and visualizes metrics using **Grafana**.

Primary device hardware:

* Arduino UNO R4 WiFi

Primary backend:

* Python + FastAPI

---

# System Components

## Backend API

Technology:

* FastAPI
* Python
* SQLModel
* APScheduler

Responsibilities:

* Manage devices
* Maintain device shadows
* Send commands to devices
* Receive telemetry
* Schedule automation tasks

---

## MQTT Broker

Technology:

* Mosquitto

Responsibilities:

* Device messaging
* Command delivery
* Telemetry transport

MQTT provides a **Publish-Subscribe messaging pattern**.

---

## Device Hardware

Hardware:

* Arduino UNO R4 WiFi

Device responsibilities:

* Subscribe to command topics
* Publish telemetry
* Publish reported state
* Send heartbeat messages

---

## Databases

### Operational Database

Technology:

PostgreSQL

Stores system state.

Tables:

```
devices
device_shadows
commands
```

Example shadow:

```
device_id: tank1
desired: {"light":"on"}
reported: {"light":"off"}
version: 5
```

---

### Telemetry Database

Technology:

TimescaleDB (PostgreSQL extension)

Stores time-series telemetry.

Example table:

```
telemetry
device_id
temperature
timestamp
```

---

## Grafana

Used for:

* temperature monitoring
* device health dashboards
* historical metrics

Grafana queries TimescaleDB directly.

---

# Messaging Architecture

## MQTT Topics

```
tankctl/{device_id}/command
tankctl/{device_id}/reported
tankctl/{device_id}/telemetry
tankctl/{device_id}/heartbeat
```

Example:

```
tankctl/tank1/command
tankctl/tank1/telemetry
```

---

# Message Formats

## Command

```
{
  "version": 7,
  "command": "set_light",
  "value": "on"
}
```

Devices must ignore commands with older versions.

---

## Telemetry

```
{
  "temperature": 24.6,
  "timestamp": 1710000000
}
```

---

## Reported State

```
{
  "light": "on"
}
```

---

# Device Shadow Model

Each device has a shadow state.

Structure:

```
DeviceShadow
 ├ desired
 ├ reported
 └ version
```

Example:

```
desired:  {"light":"on"}
reported: {"light":"off"}
version:  6
```

Shadow reconciliation ensures device state eventually matches the desired state.

---

# Scheduling System

Technology:

APScheduler

Used for:

* scheduled light toggling
* shadow reconciliation
* device heartbeat checks

Example scheduled automation:

```
light_on at 18:00
light_off at 06:00
```

---

# Telemetry Pipeline

Telemetry flow:

```
Arduino Device
        ↓
MQTT Broker
        ↓
TankCtl Backend MQTT Consumer
        ↓
TimescaleDB
        ↓
Grafana Dashboard
```

This architecture is simple and reliable for small-to-medium IoT systems.

---

# Backend Architecture

TankCtl uses a **layered architecture**.

```
API Layer
   ↓
Service Layer
   ↓
Domain Models
   ↓
Repository Layer
   ↓
Infrastructure Layer
```

Rules:

* API must not access MQTT directly
* API must not access DB directly
* Services contain business logic

---

# Project Structure

```
tankctl/

api/
domain/
services/
repository/
infrastructure/
device/
config/
utils/

main.py
```

---

# Scheduler Jobs

Periodic jobs:

```
shadow reconciliation
device heartbeat monitor
scheduled lighting control
```

---

# Reliability

System guarantees:

* commands retried if device offline
* device state stored in shadow
* telemetry persisted
* dashboards available via Grafana

---

# Deployment

Recommended deployment via Docker.

Services:

```
tankctl-backend
mosquitto
postgres
timescaledb
grafana
```

All components can run on a single server.

---

# Design Goals

TankCtl prioritizes:

* simplicity
* reliability
* MQTT-first communication
* easy device integration

It is **not intended to be a full cloud IoT platform**.
