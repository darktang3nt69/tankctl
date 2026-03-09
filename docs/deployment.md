# DEPLOYMENT.md

## Overview

TankCtl is deployed as a **containerized system** using Docker.
All services run locally or on a single server.

The system consists of:

* TankCtl backend
* Mosquitto MQTT broker
* PostgreSQL database
* TimescaleDB extension
* Grafana dashboard

---

# System Architecture

```text
Arduino Devices
      │
      ▼
 Mosquitto MQTT
      │
      ▼
 TankCtl Backend
      │
 ┌────┴─────┐
 │          │
PostgreSQL  TimescaleDB
 │
 ▼
Grafana
```

---

# Required Services

| Service         | Purpose               |
| --------------- | --------------------- |
| tankctl-backend | API + device control  |
| mosquitto       | MQTT messaging        |
| postgres        | operational database  |
| timescaledb     | telemetry database    |
| grafana         | monitoring dashboards |

---

# Docker Compose Setup

Example `docker-compose.yml`.

```yaml
version: "3.8"

services:

  mosquitto:
    image: eclipse-mosquitto
    ports:
      - "1883:1883"
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf

  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: tankctl
      POSTGRES_PASSWORD: tankctl
      POSTGRES_DB: tankctl
    ports:
      - "5432:5432"

  timescaledb:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_USER: tankctl
      POSTGRES_PASSWORD: tankctl
      POSTGRES_DB: telemetry
    ports:
      - "5433:5432"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"

  tankctl-backend:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - mosquitto
      - postgres
      - timescaledb
```

---

# Environment Variables

Backend configuration:

```text
MQTT_HOST=mosquitto
MQTT_PORT=1883

POSTGRES_HOST=postgres
POSTGRES_DB=tankctl

TIMESCALE_HOST=timescaledb
TIMESCALE_DB=telemetry
```

---

# Running the System

Start services:

```bash
docker compose up -d
```

Check services:

```bash
docker compose ps
```

---

# Grafana Setup

Open:

```
http://localhost:3000
```

Default credentials:

```
admin
admin
```

Add data source:

```
TimescaleDB
```

Example query:

```sql
SELECT
  time,
  temperature
FROM telemetry
WHERE device_id='tank1'
ORDER BY time
```

---

# Backend Startup

Run backend locally:

```bash
uvicorn main:app --reload
```

API available at:

```
http://localhost:8000
```

---

# Mosquitto Configuration

Example `mosquitto.conf`.

```text
listener 1883
allow_anonymous true
```

Authentication can be added later.

---

# Deployment Options

Supported deployments:

| Environment              | Support  |
| ------------------------ | -------- |
| Local development        | Yes      |
| Single-server production | Yes      |
| Kubernetes               | Possible |
| Cloud deployment         | Possible |

---

# Monitoring

Grafana dashboards can visualize:

* device temperature
* device uptime
* device heartbeat
* command activity

---

# Upgrade Strategy

When updating TankCtl:

1. stop containers
2. update backend image
3. restart services

Example:

```bash
docker compose down
docker compose up -d
```

---

# Design Goals

The deployment model prioritizes:

* simplicity
* single-server deployment
* container isolation
* easy upgrades
