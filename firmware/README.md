---
title: README
type: note
permalink: tankctl/firmware/readme
---

# TankCtl Arduino Firmware

Arduino firmware for TankCtl smart aquarium light control system.

## Hardware Requirements

- **Arduino UNO R4 WiFi**
- **Relay module** (connected to pin D5) for light control
- **DS18B20 temperature sensor** (optional, connected to pin D6)

## Features

- ✅ WiFi connectivity with auto-reconnect
- ✅ MQTT communication with backend
- ✅ Command processing with versioning (prevents duplicate execution)
- ✅ Light relay control
- ✅ Temperature telemetry (DS18B20)
- ✅ Heartbeat monitoring
- ✅ Local fallback light scheduler (runs even when backend is offline)
- ✅ Persistent configuration storage in EEPROM
- ✅ NTP time synchronization

## Configuration

Edit the configuration section in `tankctl_device.ino`:

```cpp
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

#define MQTT_SERVER "192.168.1.100"
#define MQTT_PORT 1883

#define DEFAULT_TANK_ID "tank1"
```

## Building and Uploading

### Prerequisites

Install `arduino-cli`:
```bash
mkdir -p ~/.local/bin
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=~/.local/bin sh
export PATH="$HOME/.local/bin:$PATH"
```

### Build

From the project root:
```bash
./tools/build_firmware.sh
```

This will:
- Install required Arduino core (arduino:renesas_uno)
- Install required libraries (ArduinoJson, PubSubClient, NTPClient, OneWire, DallasTemperature)
- Compile the firmware
- Output binary to `.build/firmware/`

### Upload

Connect your Arduino UNO R4 WiFi via USB, then:
```bash
./tools/upload_firmware.sh
```

The script will auto-detect the Arduino port and upload the firmware.

**Manual upload:**
```bash
./tools/upload_firmware.sh /dev/ttyACM0
```

## MQTT Topics

The device uses the following topics (where `{tank_id}` is your configured tank ID):

| Topic | Direction | Purpose |
|-------|-----------|---------|
| `tankctl/{tank_id}/command` | Subscribe | Receives commands from backend |
| `tankctl/{tank_id}/reported` | Publish | Reports device state after commands |
| `tankctl/{tank_id}/telemetry` | Publish | Sends temperature readings (every 5s) |
| `tankctl/{tank_id}/heartbeat` | Publish | Device health status (every 30s) |

## Command Format

### Set Light

```json
{
  "version": 15,
  "command": "set_light",
  "value": "on"
}
```

### Set Schedule

```json
{
  "version": 20,
  "command": "set_schedule",
  "on_time": "18:00",
  "off_time": "06:00"
}
```

## Local Scheduler

The device maintains a local schedule stored in EEPROM. This allows lights to turn on/off automatically even if:
- Backend is offline
- MQTT broker is down
- WiFi connection is lost

The schedule is set via MQTT commands and survives power outages.

## EEPROM Layout

| Address | Size | Purpose |
|---------|------|---------|
| 0-31 | 32 bytes | Tank ID string |
| 32-33 | 2 bytes | Schedule ON hour |
| 34-35 | 2 bytes | Schedule ON minute |
| 36-37 | 2 bytes | Schedule OFF hour |
| 38-39 | 2 bytes | Schedule OFF minute |
| 40 | 1 byte | Schedule enabled flag |
| 41 | 1 byte | Init flag (0xA5) |

## Monitoring

Connect to serial monitor at 115200 baud to see device logs:
```
TankCtl Device Starting...
Loaded config from EEPROM. Tank ID: tank1
Connecting to WiFi: YourNetwork
WiFi connected. IP: 192.168.1.42
Synchronizing time with NTP...
Connecting to MQTT broker: 192.168.1.100
MQTT connected
Subscribed to: tankctl/tank1/command
TankCtl Device Ready
Heartbeat sent
Telemetry: temp=24.6°C
```

## Firmware Size

Current build: ~85KB (32% of program storage, 70% available)

## Libraries Used

- **WiFiS3** (built-in) - WiFi connectivity for UNO R4
- **PubSubClient** - MQTT client
- **ArduinoJson** - JSON parsing
- **NTPClient** - Time synchronization
- **OneWire** - DS18B20 communication protocol
- **DallasTemperature** - Temperature sensor interface
- **EEPROM** (built-in) - Persistent storage

## Troubleshooting

### WiFi won't connect
- Check SSID and password in config
- Verify 2.4GHz WiFi (UNO R4 doesn't support 5GHz)
- Check serial monitor for connection status

### MQTT won't connect
- Verify broker IP and port
- Check broker is running: `mosquitto -v`
- Test with: `mosquitto_sub -t 'tankctl/#' -v`

### Commands not executing
- Check command version is incrementing
- Verify topic subscription in serial monitor
- Test publishing: `mosquitto_pub -t 'tankctl/tank1/command' -m '{"version":1,"command":"set_light","value":"on"}'`

### Temperature reads -127°C
- DS18B20 not connected or not detected
- Check wiring and pull-up resistor (4.7kΩ)
- Temperature sensor is optional

## Architecture

Single-file firmware design per Arduino best practices. See [docs/arduino.md](../../docs/arduino.md) for architecture details.