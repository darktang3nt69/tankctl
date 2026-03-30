---
title: MQTT_TOPICS
type: note
permalink: tankctl/docs/backend/deployment/mqtt-topics
---

# TankCtl MQTT Topics Reference

All topics extracted from `src/infrastructure/mqtt/mqtt_client.py` and service publish calls.

## Overview

**Topic Pattern:** `tankctl/{device_id}/{channel}`

**Broker:** Mosquitto (configurable via `MQTT_BROKER_HOST`, `MQTT_BROKER_PORT`)

**Authentication:** Optional (via `MQTT_USERNAME`, `MQTT_PASSWORD`)

**QoS:** Default 1 (at-least-once delivery)

---

## Topic Subscriptions (Backend → Device)

Backend subscribes to these topics using wildcard subscriptions:

```
tankctl/+/telemetry     ← Device publishes sensor data
tankctl/+/reported      ← Device publishes state
tankctl/+/heartbeat     ← Device publishes health metrics
tankctl/+/status        ← Device publishes warnings/flags
```

---

## Topic Matrix

| Topic | Direction | Publisher | Subscriber | Message Format | Frequency | QoS | Retained |
|-------|-----------|-----------|------------|---|---|---|---|
| `tankctl/{device_id}/command` | ← | Backend Service | Device | Command JSON | On-demand | 1 | false |
| `tankctl/{device_id}/telemetry` | → | Device | Backend Service | Telemetry JSON | 10 seconds (configurable) | 1 | false |
| `tankctl/{device_id}/reported` | → | Device | Backend Service (ShadowService) | State JSON | On change or heartbeat | 1 | false |
| `tankctl/{device_id}/heartbeat` | → | Device | Backend Service (DeviceService) | Health JSON | 30 seconds (configurable) | 1 | false |
| `tankctl/{device_id}/status` | → | Device | Backend Service (AlertService) | Status/Warning JSON | On event | 1 | false |

---

# Message Schemas

## Command Topic
**`tankctl/{device_id}/command`** ← (Backend → Device)

**Publisher:** Backend service (CommandService.send_command())

**Example Payload:**
```json
{
  "command": "set_light",
  "value": "on",
  "version": 3
}
```

**Fields:**
- `command` (string): Command name (set_light, set_pump, reboot_device, request_status, set_schedule)
- `value` (string): Command parameter (e.g., "on"/"off" for set_light)
- `version` (integer): Version number for idempotency (incremented by service)

**Frequency:** On-demand (when command sent via API)

**Additional Examples:**

Set light off:
```json
{"command": "set_light", "value": "off", "version": 4}
```

Set pump on:
```json
{"command": "set_pump", "value": "on", "version": 5}
```

Reboot device:
```json
{"command": "reboot_device", "version": 6}
```

Request status:
```json
{"command": "request_status", "version": 7}
```

Set schedule:
```json
{
  "command": "set_schedule",
  "on_time": "18:00",
  "off_time": "06:00",
  "version": 8
}
```

---

## Telemetry Topic
**`tankctl/{device_id}/telemetry`** → (Device → Backend)

**Publisher:** Device firmware (every 10 seconds)

**Example Payload:**
```json
{
  "temperature": 24.5
}
```

**Fields:**
- `temperature` (float): Temperature reading in Celsius

**Frequency:** 10 seconds (TELEMETRY_INTERVAL_MS in firmware)

**Processing:**
- Backend stores in TimescaleDB `device_telemetry` table
- AlertService evaluates against thresholds
- Triggers temperature alert if out of bounds

**Additional Examples:**

ESP32 with sensor reading:
```json
{"temperature": 23.8}
```

Arduino with sensor reading:
```json
{"temperature": 25.2}
```

---

## Reported State Topic
**`tankctl/{device_id}/reported`** → (Device → Backend)

**Publisher:** Device firmware (on state change or after command execution)

**Example Payload:**
```json
{
  "light": "on"
}
```

**Fields:**
- `light` (string): "on" or "off"
- `pump` (string): "on" or "off" (optional, if device supports pump)

**Frequency:** On state change or when publishing heartbeat

**Processing:**
- ShadowService.update_reported_state() updates `device_shadows` table
- Compares with desired state for synchronization
- Publishes `shadow_synchronized` event if desired == reported

**Additional Examples:**

Light and pump state:
```json
{"light": "on", "pump": "off"}
```

Light off:
```json
{"light": "off"}
```

---

## Heartbeat Topic
**`tankctl/{device_id}/heartbeat`** → (Device → Backend)

**Publisher:** Device firmware (every 30 seconds)

**Example Payload (ESP32):**
```json
{
  "status": "online",
  "uptime_ms": 8500000,
  "rssi": -65,
  "firmware_version": "1.0.0-esp32",
  "chip": "ESP32",
  "free_heap": 120000
}
```

**Example Payload (Arduino):**
```json
{
  "status": "online",
  "uptime_ms": 3600000,
  "rssi": -72,
  "firmware_version": "1.0.0",
  "chip": "Arduino"
}
```

**Fields:**
- `status` (string): "online"
- `uptime_ms` (integer): Milliseconds since device boot
- `rssi` (integer): WiFi signal strength (dBm, negative value)
- `firmware_version` (string): Current firmware version
- `chip` (string): Device chip name (ESP32, Arduino)
- `free_heap` (integer): Available heap memory (ESP32 only)

**Frequency:** 30 seconds (HEARTBEAT_INTERVAL_MS in firmware)

**Processing:**
- DeviceService.handle_heartbeat() updates device status
- Marks device as "online" if heartbeat received
- Tracks RSSI for signal strength monitoring
- Device marked "offline" if no heartbeat for 120+ seconds

---

## Status Topic
**`tankctl/{device_id}/status`** → (Device → Backend)

**Publisher:** Device firmware (on warning/error condition)

**Example Payload:**
```json
{
  "event": "warning",
  "code": "sensor_unavailable",
  "message": "Temperature sensor not connected or reading invalid"
}
```

**Fields:**
- `event` (string): "warning" or "error"
- `code` (string): Warning code (sensor_unavailable, temperature_high, temperature_low)
- `message` (string): Human-readable description

**Frequency:** On-demand (when warning/error occurs)

**Processing:**
- AlertService evaluates and publishes events
- EventPublisher triggers notifications
- PushNotificationService sends FCM if threshold crossed

**Additional Examples:**

Temperature too high:
```json
{
  "event": "alert",
  "code": "temperature_high",
  "message": "Temperature 32°C exceeds threshold 30°C"
}
```

Sensor disconnected:
```json
{
  "event": "warning",
  "code": "sensor_unavailable",
  "message": "DS18B20 sensor not responding"
}
```

---

# Topic Subscriptions in Code

**Backend subscribes via MQTTClient.subscribe()** (in `src/infrastructure/mqtt/mqtt_client.py`)

```python
def subscribe(self) -> None:
    """Subscribe to backend topics."""
    topics_to_subscribe = [
        MQTTTopics.SUBSCRIBE_TELEMETRY,    # tankctl/+/telemetry
        MQTTTopics.SUBSCRIBE_REPORTED,     # tankctl/+/reported
        MQTTTopics.SUBSCRIBE_HEARTBEAT,    # tankctl/+/heartbeat
        MQTTTopics.SUBSCRIBE_STATUS,       # tankctl/+/status
    ]

    for topic in topics_to_subscribe:
        self.client.subscribe(topic, qos=settings.mqtt.qos)
```

---

# Topic Publishing in Code

**Backend publishes commands via CommandService** (in `src/services/command_service.py`)

```python
def send_command(self, device_id: str, command: str, value: Optional[str] = None):
    # ... validation ...
    
    # Increment version for idempotency
    command_obj.version = shadow.version + 1
    
    # Publish to MQTT
    self.mqtt.publish(
        MQTTTopics.command_topic(device_id),
        {
            "command": command,
            "value": value,
            "version": command_obj.version,
        }
    )
```

---

# Topic Wildcards

**Plus Sign (+):** Matches exactly one level

```
tankctl/+/telemetry     Matches:  tankctl/tank1/telemetry
                                  tankctl/greenhouse/telemetry
                        Does NOT: tankctl/tank1/level1/telemetry
```

**Hash (#):** Matches zero or more levels (used in device subscriptions)

Device firmware may subscribe to:
```
tankctl/tank1/#  Receives: tankctl/tank1/command
                           tankctl/tank1/any/other/level
```

---

# Example Message Flow

**Scenario: User sets light on**

```
1. Client: POST /devices/tank1/commands
   Body: {"command": "set_light", "value": "on"}

2. Backend API → CommandService.send_command()
   │
   └─ Creates Command record
   │
   └─ MQTTClient.publish("tankctl/tank1/command", {
        "command": "set_light",
        "value": "on",
        "version": 3
      })

3. Device: Receives on tankctl/tank1/command
   │
   └─ Parses JSON
   │
   └─ Executes: digitalWrite(RELAY_PIN, LOW)
   │
   └─ MQTTClient.publish("tankctl/tank1/reported", {
        "light": "on"
      })

4. Backend: Receives on tankctl/tank1/reported
   │
   └─ ShadowService.update_reported_state()
   │
   └─ Compares desired vs reported
   │
   └─ Publishes event: shadow_synchronized
   │
   └─ Database updated

5. Client: Polling GET /devices/tank1/shadow
   Response: {
     "device_id": "tank1",
     "desired": {"light": "on"},
     "reported": {"light": "on"},
     "synchronized": true
   }
```

---

# Connection & Reliability

**Keep-Alive:** 60 seconds (MQTT protocol level)

**Reconnection Logic:**
- Device attempts reconnect if connection lost (5-second retry)
- Backend reconnects automatically on broker failure

**Payload Limits:**
- Max message size: 256 KB (typical MQTT default)
- TankCtl uses small JSON payloads (~128-256 bytes)

**Retained Messages:**
- Command topic: NOT retained (must receive while online)
- Telemetry, heartbeat: NOT retained (latest only)
- No retained state on broker (handled via Device Shadow in DB)

---

# Monitoring

**Topics to Monitor:**
- Spike in `/command` frequency → Possible command loop
- Missing `/heartbeat` messages → Device offline or WiFi issue
- `/status` warnings → Temperature/sensor alerts
- Connection/disconnection logs → Network stability

**Grafana Dashboard:** Check grafana/dashboards/tankctl-telemetry-dashboard.json for visualization

---

# Reference: Topic Constants

From `src/infrastructure/mqtt/mqtt_topics.py`:

```python
class TopicChannel(str, Enum):
    COMMAND = "command"
    TELEMETRY = "telemetry"
    REPORTED = "reported"
    HEARTBEAT = "heartbeat"

class MQTTTopics:
    BASE_PATTERN = "tankctl/{device_id}/{channel}"
    
    # Subscriptions
    SUBSCRIBE_TELEMETRY = "tankctl/+/telemetry"
    SUBSCRIBE_REPORTED  = "tankctl/+/reported"
    SUBSCRIBE_HEARTBEAT = "tankctl/+/heartbeat"
    SUBSCRIBE_STATUS    = "tankctl/+/status"
```