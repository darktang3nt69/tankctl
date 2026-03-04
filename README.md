# TankCtl Backend Implementation

## Overview

TankCtl is a self-hosted IoT controller for managing water tank devices. This implementation provides a complete backend following a **layered architecture** with:

- **API Layer** (FastAPI) → Routes handle HTTP requests
- **Service Layer** → Business logic and domain operations
- **Domain Models** → Pure Python dataclasses
- **Repository Layer** → Database access patterns
- **Infrastructure Layer** → MQTT, PostgreSQL, TimescaleDB, Scheduler

## Architecture

```
API (FastAPI)
    ↓
Services (Device, Shadow, Command, Telemetry)
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
│   │   ├── device_routes.py     # Device management endpoints
│   │   └── health_routes.py      # Health check endpoints
│   └── schemas.py                 # Pydantic request/response models
├── domain/
│   ├── device.py                 # Device domain model
│   ├── device_shadow.py          # Shadow state model
│   └── command.py                # Command model
├── services/
│   ├── device_service.py         # Device business logic
│   ├── telemetry_service.py      # Telemetry handling
│   ├── command_service.py        # Command orchestration
│   └── shadow_service.py         # Shadow reconciliation
├── repository/
│   ├── device_repository.py      # Device data access
│   └── telemetry_repository.py   # Telemetry & command repositories
├── infrastructure/
│   ├── mqtt/
│   │   ├── mqtt_client.py        # MQTT connection manager
│   │   ├── mqtt_topics.py        # Topic definitions
│   │   └── handlers.py           # Message handlers
│   └── db/
│       ├── database.py           # Database session manager
│       └── models.py             # SQLAlchemy models
├── config/
│   └── settings.py               # Configuration via environment
├── utils/
│   └── logger.py                 # Structured logging
├── main.py                       # Backend entry point
└── server.py                     # FastAPI application
```

## Components

### 1. MQTT Infrastructure (`infrastructure/mqtt/`)

**mqtt_client.py**
- Connects to Mosquitto broker
- Subscribes to device topics: `tankctl/+/telemetry`, `tankctl/+/reported`, `tankctl/+/heartbeat`
- Routes messages to handlers
- Publishes commands to `tankctl/{device_id}/command`

**mqtt_topics.py**
- Topic naming conventions
- Device ID extraction from topic

**handlers.py**
- `HeartbeatHandler`: Marks devices online
- `ReportedStateHandler`: Updates device shadow
- `TelemetryHandler`: Stores sensor data

### 2. Services (`services/`)

**DeviceService**
- Device registration
- Device status tracking
- Heartbeat handling
- Health monitoring

**TelemetryService**
- Stores telemetry in TimescaleDB
- Retrieves historical metrics

**CommandService**
- Sends commands to devices
- Tracks command status
- Handles command history

**ShadowService**
- Reconciles desired vs. reported state
- Manages device shadow state
- Publishes commands when delta exists

### 3. Domain Models (`domain/`)

**Device**
- Stable device identity
- Authentication secret
- Status tracking (online/offline)
- Last seen timestamp

**DeviceShadow**
- Desired state (backend → device)
- Reported state (device → backend)
- Version number for idempotency
- Synchronization checking

**Command**
- Command name and value
- Version for idempotency
- Status tracking (pending, sent, executed, failed)

### 4. Repository Layer (`repository/`)

**DeviceRepository**
- CRUD operations for devices
- Status updates
- Last seen tracking

**DeviceShadowRepository**
- Shadow persistence
- State updates

**CommandRepository**
- Command storage
- Status tracking

**TelemetryRepository**
- Telemetry data storage in TimescaleDB
- Metric queries

### 5. Database Models (`infrastructure/db/`)

**devices**: Device registry
```sql
CREATE TABLE devices (
    device_id VARCHAR(50) PRIMARY KEY,
    device_secret VARCHAR(100) NOT NULL,
    status VARCHAR(20),
    firmware_version VARCHAR(50),
    created_at TIMESTAMP,
    last_seen TIMESTAMP
);
```

**device_shadows**: Shadow state
```sql
CREATE TABLE device_shadows (
    device_id VARCHAR(50) PRIMARY KEY,
    desired TEXT,
    reported TEXT,
    version INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**commands**: Command history
```sql
CREATE TABLE commands (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50),
    command VARCHAR(100),
    value VARCHAR(250),
    version INTEGER,
    status VARCHAR(20),
    created_at TIMESTAMP,
    sent_at TIMESTAMP,
    executed_at TIMESTAMP
);
```

**telemetry**: Time-series data (TimescaleDB)
```sql
CREATE TABLE telemetry (
    id SERIAL,
    device_id VARCHAR(50),
    timestamp TIMESTAMP,
    metric_name VARCHAR(100),
    metric_value FLOAT,
    metadata TEXT
);
SELECT create_hypertable('telemetry', 'timestamp', if_not_exists => TRUE);
```

## MQTT Topic Structure

```
tankctl/{device_id}/command        ← Backend sends commands
tankctl/{device_id}/reported       ← Device sends state
tankctl/{device_id}/telemetry      ← Device sends sensor data
tankctl/{device_id}/heartbeat      ← Device sends status
```

## Environment Configuration

```bash
# MQTT
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=tankctl
MQTT_PASSWORD=secret

# PostgreSQL (operations)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tankctl
DB_USER=tankctl
DB_PASSWORD=password

# TimescaleDB (telemetry)
TIMESCALE_HOST=localhost
TIMESCALE_PORT=5432
TIMESCALE_DB=tankctl_telemetry
TIMESCALE_USER=tankctl
TIMESCALE_PASSWORD=password

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Scheduler
SCHEDULER_ENABLED=true
DEVICE_OFFLINE_TIMEOUT=60
HEARTBEAT_CHECK_INTERVAL=30
SHADOW_RECONCILIATION_INTERVAL=60

# Logging
LOG_LEVEL=INFO
```

## API Endpoints

### Device Management

**Register Device**
```bash
POST /api/devices/register
Content-Type: application/json

{
  "device_id": "tank1",
  "device_secret": "8fa93d72c6c5a91d"
}
```

**Get Device**
```bash
GET /api/devices/{device_id}
```

**List All Devices**
```bash
GET /api/devices
```

**Get Device Shadow**
```bash
GET /api/devices/{device_id}/shadow
```

**Update Device Shadow**
```bash
PUT /api/devices/{device_id}/shadow
Content-Type: application/json

{
  "desired": {"light": "on"}
}
```

### Health Check

```bash
GET /health
```

## Running the Backend

### Option 1: Run MQTT Backend (Message Broker)

```bash
python -m src.main
```

This starts:
- MQTT connection and subscriptions
- Database initialization
- Periodic scheduler jobs
- Message handlers

### Option 2: Run FastAPI Server

```bash
python -m src.server
# or
uvicorn src.server:app --host 0.0.0.0 --port 8000 --reload
```

This provides REST API endpoints for device management.

### Option 3: Run Both (Recommended)

```bash
# Terminal 1: Backend
python -m src.main

# Terminal 2: API Server
uvicorn src.server:app --host 0.0.0.0 --port 8000
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Databases

**PostgreSQL**
```sql
CREATE DATABASE tankctl;
CREATE USER tankctl WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE tankctl TO tankctl;
```

**TimescaleDB**
```sql
CREATE DATABASE tankctl_telemetry;
CREATE USER tankctl WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE tankctl_telemetry TO tankctl;

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
```

### 3. Set Environment Variables

Create `.env`:
```bash
MQTT_BROKER_HOST=localhost
DB_HOST=localhost
TIMESCALE_HOST=localhost
# ... other settings
```

### 4. Initialize Application

```bash
python -m src.main
```

The backend will:
1. Create database tables
2. Connect to MQTT broker
3. Subscribe to device topics
4. Start periodic scheduler jobs

## Testing the System

### 1. Register a Device

```bash
curl -X POST http://localhost:8000/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "tank1",
    "device_secret": "device_secret_123"
  }'
```

### 2. Simulate Device Heartbeat

```bash
mosquitto_pub -h localhost -u tankctl -P password \
  -t "tankctl/tank1/heartbeat" \
  -m '{"status": "online", "uptime": 120}'
```

### 3. Simulate Device Telemetry

```bash
mosquitto_pub -h localhost -u tankctl -P password \
  -t "tankctl/tank1/telemetry" \
  -m '{"temperature": 24.5, "humidity": 65}'
```

### 4. Send Command to Device

```bash
curl -X POST http://localhost:8000/api/devices/tank1/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command": "set_light",
    "value": "on"
  }'
```

### 5. Mock Device Response

```bash
mosquitto_pub -h localhost -u tankctl -P password \
  -t "tankctl/tank1/reported" \
  -m '{"light": "on"}'
```

## Key Features

✓ Device registration and authentication
✓ MQTT pub/sub messaging
✓ Device shadow state management
✓ Command queuing and delivery
✓ Telemetry storage (TimescaleDB)
✓ Device health monitoring
✓ Periodic reconciliation
✓ RESTful API for management
✓ Structured logging
✓ Configuration via environment

## Deployment

Use Docker Compose to deploy all services:

```yaml
version: '3'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: tankctl
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"

  timescaledb:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_DB: tankctl_telemetry
      POSTGRES_PASSWORD: password
    ports:
      - "5433:5432"

  mosquitto:
    image: eclipse-mosquitto:latest
    ports:
      - "1883:1883"
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf

  tankctl:
    build: .
    environment:
      MQTT_BROKER_HOST: mosquitto
      DB_HOST: postgres
      TIMESCALE_HOST: timescaledb
    depends_on:
      - postgres
      - timescaledb
      - mosquitto
```

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
