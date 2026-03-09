# TankCtl

## Overview

TankCtl is a self-hosted IoT controller for managing water tank devices. The backend follows a **layered architecture** with:

- **API Layer** (FastAPI) → Routes handle HTTP requests
- **Service Layer** → Business logic and domain operations
- **Domain Models** → Pure Python dataclasses
- **Repository Layer** → Database access patterns
- **Infrastructure Layer** → MQTT, PostgreSQL, TimescaleDB, Scheduler

## Architecture

```
API (FastAPI)
    ↓
Services (Device, Shadow, Command, Telemetry, Scheduling, Alerts)
    ↓
Repositories (Database access)
    ↓
Infrastructure (MQTT, DB, Scheduler)
```

### Key Design Principles

1. **Layered Architecture**: API does not access MQTT or database directly
2. **Separation of Concerns**: Business logic in services, data access in repositories
3. **MQTT-First**: Devices communicate via MQTT topics
4. **Device Shadow Pattern**: Desired vs. reported state tracking
5. **Command Idempotency**: Commands use version numbers

## Project Structure

```
src/
├── api/
│   ├── routes/
│   │   ├── devices.py           # Device management endpoints
│   │   ├── commands.py          # Command endpoints
│   │   ├── telemetry.py         # Telemetry query endpoints
│   │   ├── events.py            # Event log endpoints
│   │   └── health.py            # Health check endpoint
│   └── schemas.py               # Pydantic request/response models
├── domain/
│   ├── device.py                # Device domain model
│   ├── device_shadow.py         # Shadow state model
│   ├── command.py               # Command model
│   ├── event.py                 # Event model
│   └── light_schedule.py        # Light schedule model
├── services/
│   ├── device_service.py        # Device business logic
│   ├── shadow_service.py        # Shadow reconciliation
│   ├── command_service.py       # Command orchestration
│   ├── telemetry_service.py     # Telemetry handling
│   ├── scheduling_service.py    # Light schedule management
│   ├── alert_service.py         # Alert thresholds and suppression
│   └── notification_service.py  # WhatsApp notifications
├── repository/
│   ├── device_repository.py     # Device & shadow data access
│   ├── telemetry_repository.py  # Telemetry & command repositories
│   └── light_schedule_repository.py
├── infrastructure/
│   ├── mqtt/
│   │   ├── mqtt_client.py       # MQTT connection manager
│   │   ├── mqtt_topics.py       # Topic definitions
│   │   └── handlers.py          # Message handlers
│   ├── db/
│   │   ├── database.py          # Database session manager
│   │   └── models.py            # SQLAlchemy models
│   ├── scheduler/
│   │   └── scheduler.py         # APScheduler periodic tasks
│   └── events/
│       └── event_publisher.py   # Internal event bus
├── config/
│   └── settings.py              # Configuration via environment
├── utils/
│   └── logger.py                # Structured logging
├── main.py                      # Backend entry point
└── server.py                    # FastAPI application
```

## Components

### 1. MQTT Infrastructure (`infrastructure/mqtt/`)

**mqtt_client.py**
- Connects to Mosquitto broker
- Subscribes to: `tankctl/+/telemetry`, `tankctl/+/reported`, `tankctl/+/heartbeat`
- Publishes commands to `tankctl/{device_id}/command`

**handlers.py**
- `HeartbeatHandler`: Marks device online, stores `uptime_ms`, `rssi`, `wifi_status`
- `ReportedStateHandler`: Updates device shadow reported state
- `TelemetryHandler`: Stores sensor data in TimescaleDB

### 2. Services (`services/`)

**DeviceService** — registration, status tracking, heartbeat handling

**ShadowService** — reconciles desired vs. reported state, publishes commands on delta

**CommandService** — sends commands, tracks command status and history

**TelemetryService** — stores and retrieves time-series sensor data

**SchedulingService** — manages light schedules per device (on/off time + days)

**AlertService** — monitors telemetry against thresholds, suppresses duplicate alerts

**NotificationService** — sends WhatsApp notifications via the whatsapp-bot sidecar

### 3. Domain Models (`domain/`)

**Device** — identity, auth secret, status (online/offline), last_seen, `uptime_ms`, `rssi`, `wifi_status`

**DeviceShadow** — desired/reported state, version number, sync check

**Command** — name, value, version, status (pending → sent → executed/failed)

**LightSchedule** — on_time, off_time, days of week, enabled flag

### 4. Scheduler (`infrastructure/scheduler/`)

Periodic APScheduler tasks:
- **Shadow reconciliation**: publishes command when desired ≠ reported
- **Offline detection**: marks devices offline after `DEVICE_OFFLINE_TIMEOUT` seconds
- **Light schedule execution**: turns light on/off at configured times

### 5. Database Models (`infrastructure/db/`)

**devices**
```sql
CREATE TABLE devices (
    device_id       VARCHAR(50) PRIMARY KEY,
    device_secret   VARCHAR(100) NOT NULL,
    status          VARCHAR(20),
    firmware_version VARCHAR(50),
    created_at      TIMESTAMP,
    last_seen       TIMESTAMP,
    uptime_ms       INTEGER,
    rssi            INTEGER,
    wifi_status     VARCHAR(50)
);
```

**device_shadows**
```sql
CREATE TABLE device_shadows (
    device_id  VARCHAR(50) PRIMARY KEY,
    desired    TEXT,
    reported   TEXT,
    version    INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**commands**
```sql
CREATE TABLE commands (
    id          SERIAL PRIMARY KEY,
    device_id   VARCHAR(50),
    command     VARCHAR(100),
    value       VARCHAR(250),
    version     INTEGER,
    status      VARCHAR(20),
    created_at  TIMESTAMP,
    sent_at     TIMESTAMP,
    executed_at TIMESTAMP
);
```

**telemetry** (TimescaleDB hypertable)
```sql
CREATE TABLE telemetry (
    id           SERIAL,
    device_id    VARCHAR(50),
    timestamp    TIMESTAMP,
    metric_name  VARCHAR(100),
    metric_value FLOAT,
    metadata     TEXT
);
```
```

## MQTT Topic Structure

```
tankctl/{device_id}/command        ← Backend sends commands
tankctl/{device_id}/reported       ← Device sends shadow state
tankctl/{device_id}/telemetry      ← Device sends sensor data
tankctl/{device_id}/heartbeat      ← Device sends status/diagnostics
```

## Environment Configuration

See [.env.example](.env.example) for the full list. Key variables:

```bash
# MQTT
MQTT_BROKER_HOST=mosquitto
MQTT_BROKER_PORT=1883
MQTT_USERNAME=tankctl
MQTT_PASSWORD=password

# PostgreSQL (operational DB)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=tankctl
POSTGRES_USER=tankctl
POSTGRES_PASSWORD=password

# TimescaleDB (telemetry DB)
TIMESCALE_HOST=timescaledb
TIMESCALE_PORT=5432
TIMESCALE_DB=tankctl_telemetry
TIMESCALE_USER=tankctl
TIMESCALE_PASSWORD=password

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Application
APP_TIMEZONE=Asia/Kolkata

# Scheduler
SCHEDULER_ENABLED=true
DEVICE_OFFLINE_TIMEOUT=60
SHADOW_RECONCILIATION_INTERVAL=10
OFFLINE_DETECTION_INTERVAL=30

# Alerts
ALERTS_ENABLED=true
ALERT_MIN_INTERVAL_SECONDS=600
ALERT_TEMPERATURE_HIGH_C=30
ALERT_TEMPERATURE_LOW_C=20

# WhatsApp notifications (optional)
WHATSAPP_ENABLED=false
WHATSAPP_BOT_URL=http://whatsapp-bot:3001/send
WHATSAPP_PHONE_NUMBER=
WHATSAPP_REQUEST_TIMEOUT_SECONDS=5

# Grafana
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=admin
```

> Use Docker service names (`mosquitto`, `postgres`, `timescaledb`) when running inside Docker. Change to `localhost` for local development outside Docker.

## API Endpoints

### Devices

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/devices` | Register a new device (auto-generates secret) |
| `GET` | `/devices` | List all devices |
| `GET` | `/devices/{device_id}` | Get device status + diagnostics |
| `GET` | `/devices/{device_id}/shadow` | Get shadow state |
| `PUT` | `/devices/{device_id}/shadow` | Update desired state |

### Commands

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/devices/{device_id}/commands` | Send a raw command |
| `GET` | `/devices/{device_id}/commands` | Get command history |
| `POST` | `/devices/{device_id}/light` | Turn light on/off |
| `POST` | `/devices/{device_id}/pump` | Turn pump on/off |
| `POST` | `/devices/{device_id}/reboot` | Reboot device |
| `POST` | `/devices/{device_id}/request-status` | Request status from device |

### Light Schedule

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/devices/{device_id}/schedule` | Create/update light schedule |
| `GET` | `/devices/{device_id}/schedule` | Get light schedule |
| `DELETE` | `/devices/{device_id}/schedule` | Delete light schedule |

### Telemetry

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/devices/{device_id}/telemetry` | Get recent telemetry |
| `GET` | `/devices/{device_id}/telemetry/{metric}` | Get specific metric history |
| `GET` | `/devices/{device_id}/telemetry/hourly/summary` | Get hourly aggregates |

### Events

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/events` | List all events |
| `GET` | `/events/devices/{device_id}` | Events for a device |
| `GET` | `/events/types` | List event types |

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |

### Examples

**Register a device**
```bash
curl -X POST http://localhost:8000/devices \
  -H "Content-Type: application/json" \
  -d '{"device_id": "tank1"}'
# Response includes auto-generated device_secret — provision this into the firmware
```

**Get device status**
```bash
curl http://localhost:8000/devices/tank1
```

**Turn light on**
```bash
curl -X POST http://localhost:8000/devices/tank1/light \
  -H "Content-Type: application/json" \
  -d '{"state": "on"}'
```

**Set light schedule (on at 06:00, off at 22:00, every day)**
```bash
curl -X POST http://localhost:8000/devices/tank1/schedule \
  -H "Content-Type: application/json" \
  -d '{"on_time": "06:00", "off_time": "22:00", "days": [0,1,2,3,4,5,6], "enabled": true}'
```

**Update shadow desired state**
```bash
curl -X PUT http://localhost:8000/devices/tank1/shadow \
  -H "Content-Type: application/json" \
  -d '{"desired": {"light": "on"}}'
```

## Running with Docker (Recommended)

```bash
# Copy and edit environment config
cp .env.example .env

# Start all services
docker compose up -d

# Run database migrations
docker exec -i tankctl-postgres psql -U tankctl -d tankctl < migrations/001_create_tables.sql
docker exec -i tankctl-postgres psql -U tankctl -d tankctl < migrations/002_add_device_heartbeat_diagnostics.sql
```

Services started:
- `tankctl-postgres` — PostgreSQL on port 5432
- `tankctl-timescaledb` — TimescaleDB on port 5432 (internal)
- `tankctl-mosquitto` — MQTT broker on port 1883
- `tankctl-backend` — FastAPI + MQTT backend on port 8000
- `tankctl-grafana` — Grafana dashboards on port 3000
- `tankctl-whatsapp-bot` — WhatsApp notification bot on port 3001

## Running Locally (without Docker)

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env: change all hosts to 'localhost'
python -m src.main
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Start Services

```bash
docker compose up -d
```

### 4. Run Migrations

```bash
docker exec -i tankctl-postgres psql -U tankctl -d tankctl < migrations/001_create_tables.sql
docker exec -i tankctl-postgres psql -U tankctl -d tankctl < migrations/002_add_device_heartbeat_diagnostics.sql
```

## Testing the System

### 1. Register a Device

```bash
curl -X POST http://localhost:8000/devices \
  -H "Content-Type: application/json" \
  -d '{"device_id": "tank1"}'
# Save the device_secret from the response — provision it into firmware
```

### 2. Simulate Device Heartbeat

```bash
mosquitto_pub -h localhost -u tankctl -P password \
  -t "tankctl/tank1/heartbeat" \
  -m '{"status": "online", "uptime_ms": 12000, "rssi": -55, "wifi": "WL_CONNECTED"}'
```

### 3. Simulate Device Telemetry

```bash
mosquitto_pub -h localhost -u tankctl -P password \
  -t "tankctl/tank1/telemetry" \
  -m '{"temperature": 24.5, "humidity": 65}'
```

### 4. Send Command to Device

```bash
curl -X POST http://localhost:8000/devices/tank1/light \
  -H "Content-Type: application/json" \
  -d '{"state": "on"}'
```

### 5. Mock Device Response

```bash
mosquitto_pub -h localhost -u tankctl -P password \
  -t "tankctl/tank1/reported" \
  -m '{"light": "on"}'
```

## Key Features

✓ Device registration (auto-generated secrets)
✓ MQTT pub/sub messaging
✓ Device shadow state management (desired vs. reported)
✓ Command queuing and delivery with version idempotency
✓ Telemetry storage in TimescaleDB
✓ Device health monitoring and offline detection
✓ Periodic shadow reconciliation
✓ Light scheduling (on/off time per day of week)
✓ Temperature and metric alerting with suppression
✓ WhatsApp notifications via sidecar bot
✓ Heartbeat diagnostics (uptime, RSSI, WiFi status)
✓ Grafana dashboards
✓ RESTful API
✓ Structured logging
✓ Configuration via environment variables

## Deployment

```bash
docker compose up -d
```

All services are defined in [docker-compose.yml](docker-compose.yml) with `restart: unless-stopped` and health checks.

## Error Handling

- **Device not found**: Returns 404
- **Device already registered**: Returns 409
- **MQTT connection failed**: Logs error, retries with backoff
- **Database errors**: Logs error, raises HTTPException 500
- **Telemetry storage errors**: Logs error, continues processing

## Logging

Structured JSON logging with fields:
- `timestamp`: ISO 8601 timestamp
- `event`: Event name (e.g., "device_registered")
- `device_id`: Device ID (if applicable)
- Additional metadata as key-value pairs

Example:
```json
{
  "timestamp": "2024-03-04T10:30:45.123456",
  "event": "device_heartbeat_received",
  "device_id": "tank1",
  "status": "online"
}
```

## Performance Considerations

1. **MQTT QoS Levels**:
   - Commands: QoS 1 (at least once)
   - Telemetry: QoS 0 (fire and forget)

2. **Database Indexes**: Add indexes on `device_id`, `timestamp` for queries

3. **Telemetry Retention**: Use TimescaleDB policies for data retention

4. **Connection Pooling**: SQLAlchemy connection pool configured

## Extension Points

1. **New MQTT Topics**: Add to `mqtt_topics.py`, create handler
2. **New Services**: Follow pattern in `services/`
3. **New API Routes**: Create in `api/routes/`, include in `server.py`
4. **Custom Domain Models**: Add to `domain/`
5. **New Database Tables**: Add to `infrastructure/db/models.py`

## References

See architecture documents:
- [docs/ARCHITECTURE.md](../docs/architecture.md)
- [docs/MQTT_TOPICS.md](../docs/MQTT_TOPICS.md)
- [docs/DEVICES.md](../docs/devices.md)
- [docs/COMMANDS.md](../docs/commands.md)
- [docs/EVENTS.md](../docs/events.md)
