---
title: Backend API Layers
type: reference
permalink: tankctl/backend/backend-api-layers
tags:
- backend
- architecture
- layers
---

## Backend Implementation Layers

### 1. API Layer (`src/api/`)
- **FastAPI routes** in `routes/` directory
- **Pydantic schemas** in `schemas.py`
- Handles HTTP endpoints only
- Never touches database or MQTT directly

### 2. Service Layer (`src/services/`)
- Contains business logic
- Coordinates repositories and infrastructure
- Examples:
  - `device_service.py` - Device management
  - `shadow_service.py` - Device shadow reconciliation
  - `command_service.py` - Device command handling

### 3. Repository Layer (`src/repository/`)
- Data access abstraction
- Database CRUD operations
- Examples:
  - `device_repository.py`
  - `shadow_repository.py`
  - `telemetry_repository.py`

### 4. Infrastructure (`src/infrastructure/`)
- **MQTT** - `mqtt/` folder with PubSubClient
- **Database** - `db/database.py` SQLAlchemy setup
- **Scheduler** - APScheduler for periodic tasks
- External system adapters

### 5. Domain (`src/domain/`)
- Pure dataclasses/pydantic models
- No framework dependencies
- Examples:
  - `device.py` - Device entity
  - `device_shadow.py` - Shadow model
  - `command.py` - Command entity
  - `event.py` - Event models

### Scheduler Tasks (APScheduler)
- Shadow reconciliation
- Device heartbeat monitoring
- Retry failed commands
- Telemetry cleanup
- Water schedule reminders