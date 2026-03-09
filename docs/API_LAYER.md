## TankCtl API Layer Implementation

The API layer provides a complete RESTful interface for device management using FastAPI with async/await support.

### Architecture Overview

```
FastAPI Application
├── Lifespan Context Manager (startup/shutdown)
├── CORS Middleware
├── Dependency Injection (database sessions)
└── Route Handlers
    ├── /health (GET) - Health check
    ├── /devices (GET, POST) - Device management
    ├── /devices/{device_id}/shadow (GET, PUT) - Shadow state
    ├── /devices/{device_id}/telemetry (GET) - Telemetry data
    ├── /devices/{device_id}/commands (GET, POST) - Commands
    ├── /devices/{device_id}/light (POST) - Light control
    └── /devices/{device_id}/pump (POST) - Pump control
```

### API Endpoints

#### Health Check
```
GET /health
GET /

Response:
{
  "status": "healthy",
  "message": "TankCtl API is running"
}
```

#### Device Management

**List Devices**
```
GET /devices

Response:
{
  "count": 2,
  "devices": [
    {
      "device_id": "tank1",
      "status": "online",
      "firmware_version": "1.2.3",
      "created_at": 1701234567,
      "last_seen": 1701234890
    }
  ]
}
```

**Register Device**
```
POST /devices

Request:
{
  "device_id": "tank2",
  "device_secret": "my_secret_key"
}

Response:
{
  "device_id": "tank2",
  "status": "offline",
  "firmware_version": null,
  "created_at": 1701234567,
  "last_seen": null
}
```

**Get Device**
```
GET /devices/{device_id}

Response:
{
  "device_id": "tank1",
  "status": "online",
  "firmware_version": "1.2.3",
  "created_at": 1701234567,
  "last_seen": 1701234890
}
```

#### Shadow Management

**Get Shadow**
```
GET /devices/{device_id}/shadow

Response:
{
  "device_id": "tank1",
  "desired": {"pump": "on", "light": "off"},
  "reported": {"pump": "off", "light": "off"},
  "version": 5,
  "synchronized": false
}
```

**Update Shadow**
```
PUT /devices/{device_id}/shadow

Request:
{
  "desired": {"pump": "on"}
}

Response:
{
  "device_id": "tank1",
  "desired": {"pump": "on", "light": "off"},
  "reported": {"pump": "off", "light": "off"},
  "version": 6,
  "synchronized": false
}
```

#### Command Management

**Send Command**
```
POST /devices/{device_id}/commands

Request:
{
  "command": "set_pump",
  "value": "on"
}

Response (202 Accepted):
{
  "command_id": "tank1",
  "device_id": "tank1",
  "command": "set_pump",
  "value": "on",
  "version": 6,
  "status": "pending"
}
```

**Get Command History**
```
GET /devices/{device_id}/commands?limit=20

Response:
{
  "count": 5,
  "commands": [...]
}
```

#### Convenience Endpoints

**Set Light**
```
POST /devices/{device_id}/light

Request:
{
  "state": "on"
}

Response (202 Accepted):
{
  "command_id": "tank1",
  "device_id": "tank1",
  "command": "set_light",
  "value": "on",
  "version": 7,
  "status": "pending"
}
```

**Set Pump**
```
POST /devices/{device_id}/pump

Request:
{
  "state": "on"
}

Response (202 Accepted):
{
  "command_id": "tank1",
  "device_id": "tank1",
  "command": "set_pump",
  "value": "on",
  "version": 8,
  "status": "pending"
}
```

#### Telemetry

**Get Telemetry**
```
GET /devices/{device_id}/telemetry?limit=100

Response:
{
  "device_id": "tank1",
  "count": 5,
  "data": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "temperature": 28.5,
      "humidity": 65.2
    }
  ]
}
```

**Get Specific Metric**
```
GET /devices/{device_id}/telemetry/temperature?limit=100

Response:
{
  "device_id": "tank1",
  "metric": "temperature",
  "count": 5,
  "data": [...]
}
```

### Startup/Shutdown Lifecycle

The API uses FastAPI's lifespan context manager to coordinate startup and shutdown:

**Startup**
1. Initialize PostgreSQL database
2. Create database tables if needed
3. Connect to MQTT broker
4. Register MQTT message handlers
5. Start APScheduler for background jobs

**Shutdown**
1. Stop scheduler
2. Disconnect MQTT broker
3. Close database connections

### Dependency Injection

Routes use FastAPI's `Depends()` for dependency injection:

```python
@router.get("/devices")
def list_devices(session: Session = Depends(get_db)):
    """session is automatically injected."""
    pass
```

### Error Handling

All endpoints follow consistent error handling:

```
400 Bad Request - Invalid request format
404 Not Found - Device/resource not found
409 Conflict - Operation conflict (e.g., device already exists)
500 Internal Server Error - Server error
202 Accepted - Command received for asynchronous processing
```

### Structured Logging

All endpoints emit structured logs:

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "event": "device_registered",
  "device_id": "tank1",
  "request_id": "abc-123"
}
```

### Background Jobs

The scheduler runs two periodic tasks:

**Shadow Reconciliation (10 seconds)**
- Checks all device shadows for desired != reported
- Publishes commands to synchronize state
- Logs reconciliation events

**Device Health Check (30 seconds)**
- Checks device heartbeat status
- Marks devices offline if no heartbeat within timeout
- Logs status changes

### Configuration

Environment variables for API:

```bash
# API Server
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Scheduler
SCHEDULER_ENABLED=true
DEVICE_OFFLINE_TIMEOUT=60
SHADOW_RECONCILIATION_INTERVAL=10
OFFLINE_DETECTION_INTERVAL=30
```

### Development

**Run locally with hot reload:**
```bash
python -m uvicorn src.api.main:app --reload
```

**Access API documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Run tests:**
```bash
pytest tests/ -v
```

### OpenAPI Documentation

The API automatically generates OpenAPI (Swagger) documentation. Access via:
- `/docs` - Interactive Swagger UI
- `/redoc` - ReDoc alternative
- `/openapi.json` - Raw OpenAPI spec

This includes:
- All endpoints with examples
- Request/response schemas
- Error codes and descriptions
