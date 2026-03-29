# TankCtl API Commands Reference

All API endpoints extracted from `src/api/routes/*.py` with schemas from `src/api/schemas.py`.

## Baseline & Response Patterns

**Base URL:** `http://localhost:8000`

**Response Format:**
- Success: `200` or `201` with JSON body or empty
- Error: `400`, `404`, `409`, `500` with error detail

---

# Device Management - 9 Endpoints

## POST /devices
Register a new device

**Request:** `{"device_id": "tank1"}`

**Response (201):**
```json
{
  "device_id": "tank1",
  "device_secret": "a1b2c3d4e5f6g7h8",
  "status": "offline",
  "created_at": "2025-01-15T10:00:00+00:00"
}
```

## GET /devices
List all registered devices

**Response (200):**
```json
{
  "count": 2,
  "devices": [{"device_id": "tank1", "status": "online", ...}]
}
```

## GET /devices/{device_id}
Get device status

**Response (200):**
```json
{
  "device_id": "tank1",
  "status": "online",
  "firmware_version": "1.0.0-esp32",
  "temp_threshold_low": 22.0,
  "temp_threshold_high": 30.0
}
```

## PATCH /devices/{device_id}
Update device metadata and thresholds

**Request:**
```json
{
  "temp_threshold_low": 20.0,
  "temp_threshold_high": 28.0,
  "device_name": "Bedroom Tank"
}
```

## DELETE /devices/{device_id}
Delete device and all associated data

**Response (200):**
```json
{
  "device_id": "tank1",
  "device_deleted": true,
  "shadow_deleted": true,
  "commands_deleted": 5,
  "telemetry_deleted": 256
}
```

## GET /devices/{device_id}/detail
Get full device detail with schedules

## GET /devices/{device_id}/shadow
Get device shadow (desired + reported state)

## GET /devices/warnings/acks
Get all acknowledged warnings

## POST /devices/{device_id}/warnings/{warning_code}/ack
Acknowledge a warning

---

# Commands - 6 Endpoints

## POST /devices/{device_id}/commands
Send a command to device

**Request:**
```json
{
  "command": "set_light",
  "value": "on"
}
```

Allowed commands:
- `set_light` (value: "on" or "off")
- `set_pump` (value: "on" or "off")
- `reboot_device` (no value)
- `request_status` (no value)

**Response (202 Accepted):**
```json
{
  "command_id": "5",
  "device_id": "tank1",
  "command": "set_light",
  "value": "on",
  "version": 3,
  "status": "pending"
}
```

## GET /devices/{device_id}/commands
Get command history

**Query:** `?limit=50`

**Response (200):**
```json
{
  "count": 3,
  "commands": [{"command": "set_light", "status": "executed", ...}]
}
```

## POST /devices/{device_id}/light
Set light on/off (convenience)

**Request:** `{"state": "on"}`

## POST /devices/{device_id}/pump
Set pump on/off (convenience)

**Request:** `{"state": "off"}`

## POST /devices/{device_id}/reboot
Reboot device

## POST /devices/{device_id}/request-status
Request immediate status update

---

# Telemetry - 3 Endpoints

## GET /devices/{device_id}/telemetry
Get latest telemetry data

**Query:** `?limit=100&hours=24`

**Response (200):**
```json
{
  "device_id": "tank1",
  "count": 10,
  "data": [{
    "time": "2025-01-15T12:30:00+00:00",
    "temperature": 24.5,
    "humidity": 65.2
  }]
}
```

## GET /devices/{device_id}/telemetry/{metric}
Get specific metric (temperature, humidity, pressure)

**Query:** `?limit=50`

## GET /devices/{device_id}/telemetry/hourly/summary
Get hourly aggregated telemetry

**Query:** `?hours=24`

---

# Schedules - 5 Endpoints

## POST /devices/{device_id}/schedule
Create/update light schedule

**Request:**
```json
{
  "on_time": "18:00",
  "off_time": "06:00",
  "enabled": true
}
```

## GET /devices/{device_id}/schedule
Get light schedule

## DELETE /devices/{device_id}/schedule
Delete light schedule

## POST /devices/{device_id}/water-schedules
Add water change schedule

**Request (Weekly):**
```json
{
  "schedule_type": "weekly",
  "days_of_week": [1, 3, 5],
  "schedule_time": "12:00",
  "notes": "Water change",
  "enabled": true
}
```

**Request (Custom):**
```json
{
  "schedule_type": "custom",
  "schedule_date": "2025-02-15",
  "schedule_time": "10:00"
}
```

## GET /devices/{device_id}/water-schedules
List water change schedules

## DELETE /devices/{device_id}/water-schedules/{schedule_id}
Delete water change schedule

---

# Firmware - 3 Endpoints

## POST /firmware/upload
Upload new firmware

**Query:** `?version=2.0.0&platform=esp32&release_notes=Bug%20fixes`

**Body:** Binary file (multipart/form-data)

## GET /firmware/download/{version}
Download firmware binary

## GET /firmware/releases
List firmware releases

**Query:** `?platform=esp32`

---

# Events - 2 Endpoints

## GET /events
Get system events

**Query:** `?event_type=device_registered&device_id=tank1&limit=100`

## GET /events/devices/{device_id}
Get device-specific events

**Query:** `?limit=50`

---

# Push Notifications - 3 Endpoints

## POST /mobile/push-token
Register FCM push token

**Request:**
```json
{
  "device_id": "tank1",
  "token": "eFxN7...",
  "platform": "android"
}
```

## GET /mobile/push-token
List registered push tokens

## DELETE /mobile/push-token
Delete token or all tokens for device

**Query:** `?token=eFxN7...` or `?device_id=tank1`

---

# Health - 1 Endpoint

## GET /health
Health check (MQTT + DB status)

**Response (200):**
```json
{
  "status": "healthy",
  "message": "Backend is healthy. MQTT: connected"
}
```

---

## Statistics

- **Total Endpoints:** 30+
- **Device Management:** 9
- **Commands:** 6
- **Telemetry:** 3
- **Schedules:** 5
- **Firmware:** 3
- **Events:** 2
- **Push Notifications:** 3
- **Health:** 1