# TankCtl Architecture

## Overview

TankCtl follows a **Layered Architecture** pattern that strictly separates concerns:

```
┌─────────────────────────────────────────────────────┐
│  API Routes Layer (src/api/routes/)                  │
│  - Device management, Commands, Telemetry, etc.     │
└─────────────────┬───────────────────────────────────┘
                  │ delegates to
┌─────────────────▼───────────────────────────────────┐
│  Service Layer (src/services/)                       │
│  - Business logic, validation, orchestration        │
└─────────────────┬───────────────────────────────────┘
                  │ uses
┌─────────────────▼───────────────────────────────────┐
│  Repository + Infrastructure Layers                 │
│  ├─ Repository (src/repository/)                    │
│  │  └─ Database operations (CRUD)                   │
│  └─ Infrastructure (src/infrastructure/)            │
│     ├─ MQTT Client & Topics                         │
│     ├─ Database Connection & Models                 │
│     ├─ Event Publishing                             │
│     └─ Scheduler (APScheduler)                      │
└─────────────────────────────────────────────────────┘
```

### Core Rule

**API must NEVER directly access MQTT or Database.** All requests flow through Service → Repository/Infrastructure.

---

## API Routes Layer

Located in `src/api/routes/`

### Device Management Routes (`devices.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/devices` | GET | List all registered devices |
| `/devices` | POST | Register new device |
| `/devices/{device_id}` | GET | Get device status |
| `/devices/{device_id}` | PATCH | Update device metadata (thresholds, name, location) |
| `/devices/{device_id}` | DELETE | Delete device and associated data |
| `/devices/warnings/acks` | GET | Get acknowledged warnings across devices |
| `/devices/{device_id}/warnings/{warning_code}/ack` | POST | Acknowledge a warning |
| `/devices/{device_id}/detail` | GET | Get full device detail with all schedules |
| `/devices/{device_id}/shadow` | GET | Get device shadow state (desired + reported) |

### Command Routes (`commands.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/devices/{device_id}/commands` | POST | Send command to device |
| `/devices/{device_id}/commands` | GET | Get command history |
| `/devices/{device_id}/light` | POST | Set light on/off (convenience endpoint) |
| `/devices/{device_id}/pump` | POST | Set pump on/off (convenience endpoint) |
| `/devices/{device_id}/reboot` | POST | Reboot device |
| `/devices/{device_id}/request-status` | POST | Request immediate status update |

### Telemetry Routes (`telemetry.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/devices/{device_id}/telemetry` | GET | Get telemetry (temperature, humidity) |
| `/devices/{device_id}/telemetry/{metric}` | GET | Get specific metric (temperature, humidity, pressure) |
| `/devices/{device_id}/telemetry/hourly/summary` | GET | Get hourly aggregated telemetry |

### Schedules Routes (in `devices.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/devices/{device_id}/schedule` | GET | Get light schedule |
| `/devices/{device_id}/schedule` | POST | Create/update light schedule |
| `/devices/{device_id}/schedule` | DELETE | Delete light schedule |
| `/devices/{device_id}/water-schedules` | GET | List water change schedules |
| `/devices/{device_id}/water-schedules` | POST | Add water change schedule |
| `/devices/{device_id}/water-schedules/{schedule_id}` | DELETE | Delete water change schedule |

### Other Routes

**Events** (`events.py`)
- GET `/events` — Get system events (filterable by type, device)
- GET `/events/devices/{device_id}` — Get device-specific events
- GET `/events/types` — Get available event types
- POST `/events/dismissals` — Record dismissed attention issue

**Firmware** (`firmware.py`)
- POST `/firmware/upload` — Upload new firmware
- GET `/firmware/download/{version}` — Download firmware binary
- GET `/firmware/releases` — List firmware releases

**Push Tokens** (`push_token.py`)
- POST `/mobile/push-token` — Register FCM push token
- GET `/mobile/push-token` — List registered tokens
- DELETE `/mobile/push-token` — Delete token(s)

**Health** (various)
- GET `/health` — Health check (MQTT + DB status)

---

## Service Layer

Located in `src/services/`, services contain all business logic and use repositories to access data.

### DeviceService
**File:** `device_service.py`

| Method | Purpose |
|--------|---------|
| `register_device(device_id)` | Register new device with auto-generated secret |
| `get_device(device_id)` | Fetch device by ID |
| `get_all_devices()` | List all devices |
| `update_thresholds(device_id, low, high)` | Update temperature thresholds |
| `handle_heartbeat(device_id, uptime_ms, rssi)` | Process device heartbeat |
| `handle_telemetry(device_id, payload)` | Store device telemetry |
| `get_acknowledged_warnings()` | Get all acknowledged warnings |
| `acknowledge_warning(device_id, warning_code)` | Record warning acknowledgement |

### CommandService
**File:** `command_service.py`

| Method | Purpose |
|--------|---------|
| `send_command(device_id, command, value)` | Send command to device (publishes via MQTT, increments version) |
| `get_command_history(device_id, limit)` | Get recent commands |
| `mark_command_executed(command_id)` | Mark command as executed |
| `mark_command_failed(command_id)` | Mark command as failed |

### ShadowService
**File:** `shadow_service.py`

| Method | Purpose |
|--------|---------|
| `get_shadow(device_id)` | Get device shadow (desired + reported state) |
| `set_desired_state(device_id, desired)` | Update desired state |
| `reconcile_shadow(device_id)` | Reconcile desired vs reported, publish commands if needed |
| `update_reported_state(device_id, reported)` | Update reported state from device |

### SchedulingService
**File:** `scheduling_service.py`

| Method | Purpose |
|--------|---------|
| `create_schedule(device_id, on_time, off_time, enabled)` | Create light schedule |
| `get_schedule(device_id)` | Get device light schedule |
| `update_schedule(device_id, on_time, off_time, enabled)` | Update light schedule |
| `delete_schedule(device_id)` | Delete light schedule |

### TelemetryService
**File:** `telemetry_service.py`

| Method | Purpose |
|--------|---------|
| `get_device_telemetry(device_id, limit, hours)` | Query telemetry data |
| `get_device_metric(device_id, metric_name, limit)` | Query specific metric |
| `get_hourly_summary(device_id, hours)` | Get hourly aggregated telemetry |

### AlertService
**File:** `alert_service.py`

| Method | Purpose |
|--------|---------|
| `evaluate_alerts(device_id)` | Check telemetry against thresholds |
| `get_active_alerts(device_id)` | Get active alerts |

### PushNotificationService
**File:** `push_notification_service.py`

| Method | Purpose |
|--------|---------|
| `upsert_device_token(device_id, token, platform)` | Register or update FCM token |
| `send_notification(device_id, title, body)` | Send FCM push notification |
| `send_batch_notifications(notification_list)` | Send multiple notifications |

### WaterScheduleReminderService
**File:** `water_schedule_reminder_service.py`

| Method | Purpose |
|--------|---------|
| `schedule_reminders()` | Set up scheduled reminder jobs |
| `send_water_change_reminder(device_id)` | Send water change reminder via FCM |
| `check_and_send_reminders()` | Check if reminders need to be sent |

### FirmwareService
**File:** `firmware_service.py`

| Method | Purpose |
|--------|---------|
| `upload_firmware(file_data, version, platform, release_notes)` | Store new firmware |
| `get_firmware_file(version)` | Download firmware binary |
| `get_releases(platform)` | List firmware releases |

---

## Repository Layer

Located in `src/repository/`, repositories handle all database operations (CRUD).

### DeviceRepository (`device_repository.py`)

| Method | Purpose |
|--------|---------|
| `create(device)` | Insert new device |
| `get_by_id(device_id)` | Fetch device |
| `get_all()` | List all devices |
| `update(device)` | Update device fields |
| `delete(device_id)` | Delete device |

### DeviceShadowRepository (`device_repository.py`)

| Method | Purpose |
|--------|---------|
| `create(shadow)` | Insert shadow |
| `get_shadow(device_id)` | Fetch shadow |
| `update_desired(device_id, desired)` | Update desired state |
| `update_reported(device_id, reported)` | Update reported state |
| `increment_version(device_id)` | Increment shadow version |

### LightScheduleRepository (`light_schedule_repository.py`)

| Method | Purpose |
|--------|---------|
| `create(schedule)` | Create schedule |
| `get_by_device(device_id)` | Fetch device schedule |
| `update(schedule)` | Update schedule |
| `delete(device_id)` | Delete schedule |

### TelemetryRepository (`telemetry_repository.py`)

| Method | Purpose |
|--------|---------|
| `insert_reading(device_id, temperature, humidity, pressure, metadata)` | Store telemetry |
| `get_recent(device_id, limit)` | Fetch recent readings |
| `get_by_time_range(device_id, start, end)` | Query time range |
| `get_hourly_summary(device_id, hours)` | Get pre-aggregated summary |

### CommandRepository (`telemetry_repository.py`)

| Method | Purpose |
|--------|---------|
| `create(command)` | Insert command |
| `get_by_id(command_id)` | Fetch command |
| `get_history(device_id, limit)` | Get recent commands |
| `update_status(command_id, status)` | Update command status |

### DevicePushTokenRepository (`device_push_token_repository.py`)

| Method | Purpose |
|--------|---------|
| `upsert_token(device_id, token, platform)` | Create or update token |
| `get_by_device(device_id)` | Get tokens for device |
| `remove_token(token)` | Delete token |

---

## Infrastructure Layer

Located in `src/infrastructure/`

### MQTT Module (`src/infrastructure/mqtt/`)

**MQTTClient** (`mqtt_client.py`)
- Manages connection to Mosquitto broker
- Subscribes to device topics: telemetry, reported, heartbeat, status
- Publishes commands to devices
- Routes messages to registered handlers

**MQTTTopics** (`mqtt_topics.py`)
- Defines topic patterns: `tankctl/{device_id}/{channel}`
- Wildcard subscriptions: `tankctl/+/{channel}`
- Helper methods to extract device_id and channel from topic string

**Topic Subscriptions**
```
tankctl/+/telemetry     ← Device publishes sensor data
tankctl/+/reported      ← Device publishes state
tankctl/+/heartbeat     ← Device publishes health metrics
tankctl/+/status        ← Device publishes warnings
```

**Topic Publishes**
```
tankctl/{device_id}/command     ← Backend sends commands to device
```

### Database Module (`src/infrastructure/db/`)

**Database** (`database.py`)
- SQLAlchemy ORM session management
- Connection pooling
- Migrations via Alembic
- TimescaleDB for telemetry (time-series optimized)

**Models** (`models.py`)
- DeviceModel, DeviceShadowModel, LightScheduleModel
- CommandModel, TelemetryModel (TimescaleDB hypertable)
- WaterScheduleModel, DevicePushTokenModel
- WarningAcknowledgementModel, EventRecord

### Event Publisher (`src/infrastructure/events/`)

**EventPublisher** — In-process pub/sub for system events
- Publishes: device_registered, device_online, device_offline, alert_triggered, warning_acknowledged
- Async event handling to decouple systems

**EventStore** — Persistent event log for audit trail
- All events stored to SQLite for historical queries
- Query by event_type, device_id, timestamp

### Scheduler (`src/infrastructure/scheduler/`)

**Scheduler** — APScheduler for recurring tasks
- Shadow reconciliation every 5 minutes
- Device heartbeat monitoring every 2 minutes
- Telemetry cleanup (old records) daily
- Retry failed commands
- Water change reminders at scheduled times

---

## Data Flow Examples

### Example 1: Command Execution Pipeline

```
1. Client: POST /devices/tank1/commands
2. API Route: Validates CommandRequest
3. Service: CommandService.send_command()
   ├─ Creates Command record (pending)
   ├─ Updates Device Shadow desired state
   └─ MQTTClient.publish() to tankctl/tank1/command
4. Device: Receives & executes command
5. Device: Publishes tankctl/tank1/reported
6. Backend: ShadowService.update_reported_state()
7. Database: shadow_synchronized event
8. Client: GET /devices/tank1/commands → sees execution status
```

---

## Configuration

**Settings** (`src/config/settings.py`) — Via environment variables

- DATABASE_URL — PostgreSQL connection
- MQTT_BROKER_HOST — Mosquitto broker IP
- MQTT_BROKER_PORT — MQTT port
- FCM_PROJECT_ID — Firebase project ID
- SCHEDULER_ENABLED — Enable APScheduler

---

## Summary

- **Clean Layers:** API → Service → Repository → DB
- **Event-Driven:** System events for notifications and auditing
- **MQTT-First:** Device communication via publish-subscribe
- **Device Shadow:** Tracks desired vs reported state with automatic reconciliation
- **Resilient:** Versioning, retries, timeouts, comprehensive logging