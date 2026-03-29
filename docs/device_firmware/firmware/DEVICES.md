---
title: DEVICES
type: note
permalink: tankctl/docs/device-firmware/firmware/devices
---

# TankCtl Device Firmware Specification

All device information extracted directly from firmware source files in `firmware/esp32/tankctl_esp32.ino` and `firmware/Arduino Uno EK R4 Wifi/tankctl_device.ino`.

---

## Device Specifications

| Aspect | ESP32 | Arduino UNO R4 WiFi |
|--------|-------|---|
| **File** | `firmware/esp32/tankctl_esp32.ino` | `firmware/Arduino Uno EK R4 Wifi/tankctl_device.ino` |
| **Board** | ESP32-WROOM-32 | Renesas RA4M1 |
| **RAM** | 520 KB | 32 KB |
| **Flash** | 4 MB | 256 KB |
| **WiFi** | Native (0-20 dBm) | Built-in (0-20 dBm) |
| **MQTT** | PubSubClient + WiFi.h | PubSubClient + WiFiS3.h |
| **Temperature Sensor** | DS18B20 (OneWire) | DS18B20 (OneWire) |
| **LED/Output** | GPIO 2 (status LED) | 8x12 LED Matrix display |
| **Serial** | 9600 baud | 9600 baud |
| **NTP** | configTime() (ESP32 built-in) | NTPClient library |
| **Storage** | Preferences (NVS) | EEPROM |
| **Firmware Version** | 1.0.0-esp32 | 1.0.0 |
| **Status** | Primary | Secondary |

---

# ESP32 Firmware

## GPIO Pinout

| GPIO | Pin Name | Function | Type | Purpose | Active Level | Notes |
|------|----------|----------|------|---------|---|---|
| 4 | GPIO 4 | Relay (Light/Pump) | Output | Control relay for light or pump | LOW | Active-low relay (HIGH = OFF, LOW = ON) |
| 23 | GPIO 23 | DS18B20 Data | 1-Wire | Temperature sensor | N/A | Requires 4.7kΩ pull-up resistor |
| 2 | GPIO 2 | Status LED | Output | Device connectivity indicator | HIGH | Solid = WiFi+MQTT, Pulse = WiFi only, OFF = no WiFi |

## Pin Configuration (from code)

```cpp
#define RELAY_PIN 4        // GPIO 4: Relay (active-low)
#define ONE_WIRE_PIN 23    // GPIO 23: DS18B20 temperature sensor
#define STATUS_LED_PIN 2   // GPIO 2: Status LED (optional)
```

## Initialization

```cpp
pinMode(RELAY_PIN, OUTPUT);
digitalWrite(RELAY_PIN, HIGH);  // Relay OFF (active-low)

pinMode(STATUS_LED_PIN, OUTPUT);
digitalWrite(STATUS_LED_PIN, LOW);  // LED OFF initially

sensors.begin();  // OneWire temperature sensor
sensors.setResolution(TEMP_SENSOR_RESOLUTION_BITS);  // 10-bit resolution
```

---

# Arduino UNO R4 WiFi Firmware

## GPIO Pinout

| Pin | Function | Type | Purpose | Notes |
|-----|----------|------|---------|-------|
| 4 | Relay (Light/Pump) | Output | Control relay | Active-low |
| 6 | DS18B20 Data | 1-Wire | Temperature sensor | OneWire library |
| Built-in | LED Matrix | Output | Display light state | 8x12 pixel matrix |

## Pin Configuration (from code)

```cpp
#define RELAY_PIN 4 // Using pin 4 for the relay
#define ONE_WIRE_PIN 6  // OneWire temperature sensor
```

## EEPROM Memory Map

| Address | Size | Purpose |
|---------|------|---------|
| 0 | 32 B | Tank ID |
| 32 | 2 B | Schedule on hour |
| 34 | 2 B | Schedule on minute |
| 36 | 2 B | Schedule off hour |
| 38 | 2 B | Schedule off minute |
| 40 | 1 B | Schedule enabled flag |
| 41 | 1 B | Init flag (0xA5) |
| 100 | 64 B | Device secret |
| 164 | 1 B | Device registered flag |

## LED Matrix Display

Shows device light state via LED matrix (8x12 pixels):

**Light ON:** Display "ON" pattern
```
  ┌─────────────┐
  │ ● ● ●ø● ● ● │
  │ ● øøøø● ● ● │
  │ ●øø ●øø● ● ● │
  │ ● ø●●ø● ● ● │
  │ ● ● ●ø● ● ● │
  └─────────────┘
```

**Light OFF:** Display "OFF" pattern
```
  ┌─────────────┐
  │ ● ● ●ø● ● ● │
  │ ● øø ø● ø ø  │
  │ ● ø● ø● ● ø  │
  │ ● øø ø● ø ø  │
  │ ● ● ●ø● ø ø  │
  └─────────────┘
```

---

# Supported Commands

All commands received on `tankctl/{device_id}/command` topic.

| Command | Parameters | Effect | Response Topic | Device Action |
|---------|-----------|--------|---|---|
| `set_light` | `value` ("on"/"off") | Turn light on/off | `tankctl/{device_id}/reported` | GPIO 4: LOW (on) or HIGH (off), publish `{"light": "on/off"}` |
| `set_pump` | `value` ("on"/"off") | Turn pump on/off | `tankctl/{device_id}/reported` | GPIO 4: LOW (on) or HIGH (off) |
| `set_schedule` | `on_time`, `off_time` | Set light schedule times | `tankctl/{device_id}/reported` | Parse, save to storage, apply schedule |
| `reboot_device` | (none) | Reboot device | `tankctl/{device_id}/heartbeat` | Publish final state, wait 300ms, call ESP.restart() or similar |
| `request_status` | (none) | Request immediate update | `tankctl/{device_id}/heartbeat` + `tankctl/{device_id}/reported` | Publish heartbeat and reported state immediately |

## Command Format & Versioning

All commands include a **version** field for idempotency:

```json
{
  "command": "set_light",
  "value": "on",
  "version": 3
}
```

**Device must:**
1. Check version number
2. Ignore commands with version <= last_command_version
3. Execute only if version > last_command_version
4. Save version for future comparisons

**Example (from ESP32 firmware):**
```cpp
void handleCommand(JsonDocument& doc) {
  uint32_t version = doc["version"];
  
  if (version <= lastCommandVersion) {
    Serial.println("Ignoring old command version");
    return;  // Ignore old command
  }
  
  lastCommandVersion = version;
  
  const char* cmd = doc["command"];
  if (strcmp(cmd, "set_light") == 0) {
    handleSetLight(doc);
  }
  // ...
}
```

---

# Water Schedule System (Backend-Driven)

## Overview

Water schedules are a **backend-only feature** that require **no firmware changes**. All device types (ESP32, Arduino UNO R4 WiFi) support water schedules automatically.

**Key Characteristics:**
- Schedules stored entirely in backend database
- Not synced to device via MQTT (unlike light schedules)
- Reminders sent via Firebase Cloud Messaging (FCM), not MQTT
- Timezone-aware (evaluated in app timezone, default IST)
- Repeatable (weekly recurring or custom one-time schedules)

## Schedule Types

### Weekly Recurring
```json
{
  "schedule_type": "weekly",
  "days_of_week": [1, 3, 5],  // Monday, Wednesday, Friday
  "schedule_time": "12:00"    // Noon
}
```
Repeats every week on specified days at specified time.

### Custom Single-Date
```json
{
  "schedule_type": "custom",
  "schedule_date": "2025-02-28",
  "schedule_time": "14:30"
}
```
Fires once on specified date at specified time.

## Notification Reminders

Backend evaluates schedules every minute and sends FCM reminders at three pre-defined offsets:

| Reminder Type | Trigger | Condition | Message |
|---|---|---|---|
| **24-Hour** | 24 hours before scheduled time | If `notify_24h=true` | "💧 Water Change Tomorrow — {device_name}" |
| **1-Hour** | 1 hour before scheduled time | If `notify_1h=true` | "💧 Water Change in 1 Hour — {device_name}" |
| **On-Time** | At exact scheduled time | If `notify_on_time=true` | "🪣 Time to Change Water — {device_name}" |

**Important:** Notifications require device to have registered FCM push tokens via mobile app.

## API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/devices/{device_id}/water-schedules` | GET | List all schedules |
| `/devices/{device_id}/water-schedules` | POST | Create schedule (weekly or custom) |
| `/devices/{device_id}/water-schedules/{id}` | PUT | Update schedule (partial or full) |
| `/devices/{device_id}/water-schedules/{id}` | DELETE | Delete schedule |

See `docs/backend/commands/commands.md` for full endpoint specifications and schema.

## Timezone Handling

- All times treated as wall-clock times in **app timezone** (default: `Asia/Kolkata` / IST)
- No explicit timezone in database (assumes app timezone)
- Reminder evaluation compares schedule time against `datetime.now(app_tz)`
- Example: Schedule at `12:00` → reminder fires when local time reaches `12:00` in IST

## No Device Firmware Changes Needed

Water schedules are pure backend feature:
- Device firmware does **not** need updates
- No new MQTT topics or commands
- Existing devices automatically support water schedules
- Reminders handled entirely by backend scheduler

---

# MQTT Publish Flow

## Telemetry Publishing

**Topic:** `tankctl/{device_id}/telemetry`

**Interval:** 10 seconds (`TELEMETRY_INTERVAL_MS`)

**Payload:**
```json
{
  "temperature": 24.5
}
```

**Code (ESP32):**
```cpp
#define TELEMETRY_INTERVAL_MS 10000UL

void publishTelemetry() {
  if (!mqttClient.connected()) return;
  
  // Read DS18B20 sensor (async, takes ~200ms)
  float tempReading = sensors.getTempCByIndex(0);
  temperature = tempReading;
  
  StaticJsonDocument<128> doc;
  doc["temperature"] = temperature;
  
  char buffer[128];
  serializeJson(doc, buffer);
  mqttClient.publish(topicTelemetry, buffer);
}
```

**Frequency Details:**
- Sensor reading: Non-blocking async (requestTemperatures → wait 200ms → getTempCByIndex)
- Data published only when reading complete
- Loop runs continuously, telemetry published every 10 seconds

## Reported State Publishing

**Topic:** `tankctl/{device_id}/reported`

**Trigger:** On state change OR every heartbeat

**Payload:**
```json
{
  "light": "on"
}
```

**Code (ESP32):**
```cpp
void setLight(bool state) {
  lightState = state;
  digitalWrite(RELAY_PIN, state ? LOW : HIGH);  // Active-low relay
  publishReportedState();
}

void publishReportedState() {
  StaticJsonDocument<128> doc;
  doc["light"] = lightState ? "on" : "off";
  
  char buffer[128];
  serializeJson(doc, buffer);
  mqttClient.publish(topicReported, buffer);
}
```

## Heartbeat Publishing

**Topic:** `tankctl/{device_id}/heartbeat`

**Interval:** 30 seconds (`HEARTBEAT_INTERVAL_MS`)

**Payload (ESP32):**
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

**Payload (Arduino):**
```json
{
  "status": "online",
  "uptime_ms": 3600000,
  "rssi": -72,
  "firmware_version": "1.0.0",
  "chip": "Arduino"
}
```

**Code (ESP32):**
```cpp
#define HEARTBEAT_INTERVAL_MS 30000UL

void publishHeartbeat() {
  if (!mqttClient.connected()) return;
  
  StaticJsonDocument<128> doc;
  doc["status"] = "online";
  doc["uptime_ms"] = millis();
  doc["rssi"] = WiFi.RSSI();
  doc["firmware_version"] = FIRMWARE_VERSION;
  doc["chip"] = "ESP32";
  doc["free_heap"] = ESP.getFreeHeap();
  
  char buffer[128];
  serializeJson(doc, buffer);
  mqttClient.publish(topicHeartbeat, buffer);
}
```

---

# Memory Footprint & Allocation

Extracted from firmware source:

## ESP32 Allocations

| Allocation | Size | Purpose | Constraint |
|-----------|------|---------|---|
| tankId (char[]) | 32 B | Device ID storage | Preferences (NVS) |
| deviceSecret (char[]) | 64 B | Auth secret | Preferences (NVS) |
| JSON Document | 256 B | Command parsing | StaticJsonDocument<256> |
| Telemetry Buffer | 128 B | Telemetry JSON | Local stack |
| Global State | ~100 B | lastseen times, flags | Global variables |
| **Total Static** | ~580 B | Core allocations | Heap: 520 KB available |

## Arduino Allocations

| Allocation | Size | Purpose | Constraint |
|-----------|------|---------|---|
| tankId (char[]) | 32 B | Device ID | EEPROM |
| deviceSecret (char[]) | 64 B | Auth secret | EEPROM |
| JSON Document | 256 B | Command parsing | StaticJsonDocument<256> |
| LED Matrix Buffer | 96 B | Display state | Built-in |
| **Total Static** | ~448 B | Core allocations | EEPROM: 1 KB available, RAM: 32 KB |

**Key Constraint:** Arduino has limited RAM. Use only `StaticJsonDocument` (no dynamic String class).

---

# Connection & Resilience

## WiFi Connection Logic

**Retry Interval:** 5 seconds (`WIFI_RETRY_INTERVAL_MS`)

**Connection Attempt Timeout:** 10 seconds (20 × 500ms)

**Code (ESP32):**
```cpp
#define WIFI_RETRY_INTERVAL_MS 5000UL

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi connected. IP: ");
    Serial.println(WiFi.localIP());
  }
}
```

**Resilience Features:**
- Continuous WiFi monitoring in main loop
- Automatic reconnection if connection lost
- Status LED updates to show WiFi state
- Device still functions offline (local schedule continues)

## MQTT Connection Logic

**Retry Interval:** 3 seconds (`MQTT_RETRY_INTERVAL_MS`)

**Connection Only When:**
- WiFi is connected
- Will attempt reconnect if WiFi regained

**Code (ESP32):**
```cpp
#define MQTT_RETRY_INTERVAL_MS 3000UL

void connectMQTT() {
  if (mqttClient.connected()) return;
  if (WiFi.status() != WL_CONNECTED) return;
  
  char clientId[48];
  snprintf(clientId, sizeof(clientId), "tankctl-esp32-%s", tankId);
  
  mqttClient.connect(clientId, MQTT_SERVER, MQTT_PORT);
}
```

**Resilience Features:**
- Automatic reconnection after WiFi restored
- Command queue: commands received while offline will execute when reconnected
- Heartbeat tracking: backend marks device offline if no heartbeat for 120s

## Temperature Sensor Resilience

**Async Non-Blocking Reading:**
```cpp
// Request reading (takes ~200ms)
sensors.requestTemperatures();
tempConversionInProgress = true;

// Later, when conversion complete:
float tempReading = sensors.getTempCByIndex(0);

// Validate reading
if (tempReading != DEVICE_DISCONNECTED_C && 
    tempReading > -55.0 && tempReading < 125.0) {
  temperature = tempReading;  // Valid
} else {
  temperature = 0;  // Sensor error
  publishWarning("sensor_unavailable");
}
```

**Disconnection Detection:**
- DEVICE_DISCONNECTED_C (-127) indicates sensor not connected
- Out-of-range readings (< -55°C or > 125°C) indicate error
- Publishes warning to `tankctl/{device_id}/status` topic
- Backend alerts user via mobile notification

---

# Device Registration Flow

**At Startup:**

1. Load device_id and device_secret from storage (Preferences/EEPROM)
2. If not registered:
   ```cpp
   GET /devices (registration_server)
   POST /{device_id}
   Receive: device_secret  
   Save to storage
   ```
3. Connect WiFi
4. Connect MQTT
5. Begin publishing telemetry & heartbeat

**Auto Configuration:**
- Light schedule defaults: 2 PM (14:00) ON → 8 PM (20:00) OFF
- Temperature thresholds: Backend sets default (22°C to 30°C)
- Device receives thresholds via heartbeat response or command

---

# Time Synchronization

**NTP Update Interval:** 3600 seconds (1 hour) (`NTP_UPDATE_INTERVAL_MS`)

**ESP32:**
```cpp
#define TIMEZONE_OFFSET_SECONDS 19800  // UTC+5:30 (IST)
#define TIMEZONE_NAME "Asia/Kolkata"

configTime(TIMEZONE_OFFSET_SECONDS, 0, "pool.ntp.org", "time.nist.gov");
```

**Arduino:**
```cpp
NTPClient timeClient(ntpUDP, "pool.ntp.org", TIMEZONE_OFFSET_SECONDS, 60000);
timeClient.begin();
timeClient.update();  // Call in loop
```

**Local Schedule Execution:**

Even without MQTT, device runs local schedule:
```cpp
void runSchedule() {
  if (!scheduleEnabled) return;
  
  time_t now = time(nullptr);
  struct tm* timeinfo = localtime(&now);
  
  int currentHour = timeinfo->tm_hour;
  int currentMin = timeinfo->tm_min;
  
  // Check if current time matches schedule
  if (currentHour == scheduleOnHour && currentMin == scheduleOnMinute) {
    setLight(true);  // Turn ON
  }
  // ... check OFF time ...
}
```

---

# Build Configuration

## For ESP32

Required libraries (Arduino IDE):
- WiFi.h (built-in)
- PubSubClient.h (mqtt)
- ArduinoJson.h (json)
- OneWire.h (1-Wire protocol)
- DallasTemperature.h (DS18B20 sensor)

Configuration header:
```cpp
#define WIFI_SSID "YOUR_SSID"
#define WIFI_PASSWORD "YOUR_PASSWORD"
#define MQTT_SERVER "192.168.1.100"
#define MQTT_PORT 1883
#define REGISTRATION_SERVER "192.168.1.100"
#define REGISTRATION_PORT 8000
#define DEFAULT_TANK_ID "POND-ESP32"
#define FIRMWARE_VERSION "1.0.0-esp32"
```

## For Arduino UNO R4 WiFi

Required libraries:
- WiFiS3.h (built-in)
- PubSubClient.h (mqtt)
- ArduinoJson.h (json)
- OneWire.h (1-Wire)
- DallasTemperature.h (DS18B20)
- EEPROM.h (built-in)
- NTPClient.h (time)
- WiFiUdp.h (built-in)
- Arduino_LED_Matrix.h (LED display)

---

# Debugging & Diagnostics

**Serial Output (9600 baud):**

Startup log:
```
=== TankCtl ESP32 Device Starting ===
Using DS18B20 temperature sensor
Connecting to WiFi: EMPIRE
WiFi connected. IP: 192.168.1.105
Synchronizing time with NTP...
Connecting to MQTT broker: 192.168.1.100:1883
MQTT connected
TankCtl ESP32 Device Ready
```

Health logs (every 60 seconds):
```
Health: uptime_ms=60000 wifi=connected mqtt=connected rssi=-65
Health: uptime_ms=120000 wifi=connected mqtt=connected rssi=-63
```

Command execution:
```
Command received: set_light
Setting light to: ON (GPIO LOW)
Reported state: light=on
```

Warning example:
```
Telemetry: sensor unavailable, sending temperature=0
event=warning code=sensor_unavailable
```

---

# Typical Power Consumption

## ESP32
- Idle (WiFi on): ~50 mA
- Transmit (WiFi + MQTT): ~100-150 mA
- Sleep mode: ~10 mA (if implemented)
- **Typical 24h:** ~900 mAh (with periodic WiFi/MQTT use)

## Arduino UNO R4 WiFi
- Idle (WiFi on): ~45 mA
- Transmit: ~120 mA
- LED Matrix display: ~5 mA (minimal impact)
- **Typical 24h:** ~800 mAh

---

# LED Indicators

**ESP32 GPIO 2 LED:**
- Solid ON: WiFi + MQTT connected
- Blinking: WiFi connected, MQTT disconnected
- OFF: WiFi disconnected

**Arduino LED Matrix:**
- Shows "ON" pattern: Light is ON
- Shows "OFF" pattern: Light is OFF
- Updates on state change or command received

---

# Supported Configurations

**WiFi:** Any 2.4 GHz WiFi (WPA2, WPA3)

**MQTT:** Mosquitto broker, PubSubClient compatible

**Time Zone:** Configurable (default IST UTC+5:30)

**Temperature Sensor:** DS18B20 OneWire only (currently)

**Relay:** Any active-low relay (GPIO voltage ~3.3V for ESP32, 3.3V for Arduino)

---

# Firmware Updates (OTA)

Device checks for updates:
1. Backend publishes new firmware version via command
2. Device downloads from `/firmware/download/{version}`
3. Device validates checksum
4. Device reboots and flashes new firmware
5. Device verifies and publishes new `firmware_version` in heartbeat

(Full OTA implementation pending)