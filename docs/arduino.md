# ARDUINO.md

## Overview

This document defines the **Arduino firmware design for TankCtrl devices**.

Each Arduino device controls **one tank** and communicates with the TankCtrl backend through MQTT.

The firmware is intentionally designed to use **a single Arduino file (`.ino`)** to keep development simple and compatible with the Arduino IDE.

The device responsibilities include:

* connecting to WiFi
* connecting to MQTT
* receiving commands
* controlling the light relay
* sending telemetry (temperature)
* sending heartbeat signals
* running a **local fallback schedule**
* storing configuration in EEPROM

Supported hardware:

* Arduino UNO R4 WiFi
* relay module for light control
* DS18B20 temperature sensor (recommended)

---

# Firmware Structure

The firmware is implemented in **one Arduino sketch file**.

Example project:

```text
tankctl_device/
 └── tankctl_device.ino
```

All logic lives inside this file using logical sections.

Example structure:

```cpp
// ===== CONFIG =====

// ===== LIBRARIES =====

// ===== GLOBAL STATE =====

// ===== SETUP =====

// ===== MAIN LOOP =====

// ===== WIFI FUNCTIONS =====

// ===== MQTT FUNCTIONS =====

// ===== COMMAND HANDLER =====

// ===== TELEMETRY =====

// ===== SCHEDULER =====
```

---

# Required Libraries

The firmware uses common Arduino libraries.

```cpp
#include <WiFiS3.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <EEPROM.h>
```

Purpose of each library:

| Library           | Purpose                  |
| ----------------- | ------------------------ |
| WiFiS3            | WiFi connectivity        |
| PubSubClient      | MQTT communication       |
| ArduinoJson       | parsing command messages |
| OneWire           | DS18B20 communication    |
| DallasTemperature | temperature sensor       |
| EEPROM            | persistent storage       |

---

# Device Identity

Each controller represents a **tank** and is identified by a `tank_id`.

Example:

```text
tank1
tank2
tank3
```

The device uses this ID for all MQTT communication.

Example topic:

```text
tankctl/tank1/telemetry
```

---

# EEPROM Storage

Persistent values are stored in EEPROM.

EEPROM layout:

```text
0 - 31   tank_id
32 - 33  schedule_on_hour
34 - 35  schedule_on_minute
36 - 37  schedule_off_hour
38 - 39  schedule_off_minute
40       schedule_enabled
```

This allows the device to:

* remember identity
* remember light schedule
* survive power outages

---

# MQTT Topics

Topic pattern:

```text
tankctl/{tank_id}/{channel}
```

Channels:

```text
command
reported
telemetry
heartbeat
```

Example topics:

```text
tankctl/tank1/command
tankctl/tank1/reported
tankctl/tank1/telemetry
tankctl/tank1/heartbeat
```

---

# Device State

The firmware maintains runtime state.

Example variables:

```cpp
bool lightState = false;
float temperature = 0.0;
int lastCommandVersion = 0;

int scheduleOnHour;
int scheduleOnMinute;

int scheduleOffHour;
int scheduleOffMinute;

bool scheduleEnabled = false;
```

---

# Boot Sequence

Startup flow:

```text
device power on
   ↓
load configuration from EEPROM
   ↓
connect WiFi
   ↓
synchronize time using NTP
   ↓
connect MQTT broker
   ↓
subscribe to command topic
   ↓
publish heartbeat
   ↓
publish reported state
```

---

# WiFi Connection

The device connects to WiFi using configured credentials.

Example configuration:

```cpp
#define WIFI_SSID "your_wifi"
#define WIFI_PASS "your_password"
```

Reconnect logic is required.

```text
if WiFi disconnected
    reconnect WiFi
```

---

# MQTT Connection

MQTT broker example:

```cpp
#define MQTT_SERVER "192.168.1.10"
#define MQTT_PORT 1883
```

Client ID:

```text
tankctl-{tank_id}
```

Example:

```text
tankctl-tank1
```

After connecting the device subscribes to:

```text
tankctl/{tank_id}/command
```

---

# Command Messages

Commands arrive through MQTT.

Example payload:

```json
{
  "version": 12,
  "command": "set_light",
  "value": "on"
}
```

Processing logic:

```text
receive message
parse JSON
check command version
execute command
publish reported state
```

---

# Command Versioning

Commands include a **version number**.

Rule:

```text
if version <= lastCommandVersion
    ignore command
```

This prevents duplicate execution.

---

# Supported Commands

### Light Control

Example:

```json
{
  "version": 15,
  "command": "set_light",
  "value": "on"
}
```

Device behavior:

```text
turn relay ON
update light state
publish reported state
```

---

### Schedule Update

Example command:

```json
{
  "version": 20,
  "command": "set_schedule",
  "on_time": "18:00",
  "off_time": "06:00"
}
```

Device behavior:

```text
store schedule in memory
write schedule to EEPROM
enable local scheduling
```

---

# Local Light Scheduler

The device runs the schedule locally.

Example schedule:

```text
ON  18:00
OFF 06:00
```

Scheduler logic runs inside the main loop.

```text
check current time
if time == on_time
    turn light ON
if time == off_time
    turn light OFF
```

This ensures lights continue working even if the backend fails.

---

# Temperature Telemetry

The device periodically reads the temperature sensor.

Topic:

```text
tankctl/{tank_id}/telemetry
```

Example payload:

```json
{
  "temperature": 24.6
}
```

Recommended interval:

```text
5 seconds
```

---

# Heartbeat Messages

Heartbeat indicates device health.

Topic:

```text
tankctl/{tank_id}/heartbeat
```

Example payload:

```json
{
  "status": "online"
}
```

Recommended interval:

```text
30 seconds
```

---

# Reported State

After executing commands the device publishes its state.

Topic:

```text
tankctl/{tank_id}/reported
```

Example payload:

```json
{
  "light": "on"
}
```

The backend updates the device shadow accordingly.

---

# Main Loop Behavior

The Arduino loop performs several tasks.

Example logic:

```cpp
void loop() {

  mqttClient.loop();

  runSchedule();

  if (telemetryTimerExpired) {
      publishTelemetry();
  }

  if (heartbeatTimerExpired) {
      publishHeartbeat();
  }

}
```

---

# Reconnection Logic

The device must recover from network failures.

```text
if WiFi disconnected
    reconnect WiFi

if MQTT disconnected
    reconnect MQTT
    resubscribe command topic
```

After reconnect:

```text
publish heartbeat
publish reported state
```

---

# Light Hardware Control

Typical wiring:

```text
Arduino pin D5 → relay module → light
```

Control logic:

```text
HIGH = light ON
LOW  = light OFF
```

---

# Temperature Sensor

Recommended sensor:

```text
DS18B20
```

Advantages:

* waterproof
* accurate
* suitable for aquariums

---

# Failure Behavior

If the backend or MQTT becomes unavailable:

```text
device continues executing local schedule
```

Lights remain operational.

---

# Design Goals

The TankCtrl Arduino firmware is designed to be:

* simple
* reliable
* resilient to network failures
* compatible with device shadow architecture
* easy to maintain using the Arduino IDE
