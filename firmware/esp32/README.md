---
title: README
type: note
permalink: tankctl/firmware/esp32/readme
---

# TankCtl ESP32 Firmware

Optimized firmware for **ESP32 WROOM 32D** microcontroller.

## Key Improvements Over Arduino UNO R4

| Aspect | UNO R4 | ESP32 WROOM 32D |
|--------|--------|-----------------|
| **WiFi** | WiFiS3 module | Built-in 802.11 b/g/n |
| **RAM** | 32 KB | 520 KB |
| **Flash** | 256 KB | 4 MB |
| **CPU** | 48 MHz | 240 MHz (dual-core capable) |
| **WiFi Speed** | Slower, less stable | Much faster, more reliable |
| **Storage** | Limited EEPROM | NVS (up to 16 MB) |
| **Power** | Lower power draw | Moderate (3.3V) |

## Hardware Pinout (ESP32 WROOM 32D)

```
Relay Control    → GPIO 4
Temperature      → GPIO 23 (1-Wire)
Status LED       → GPIO 2 (optional, built-in on many boards)
```

### Wiring Diagram

```
ESP32 Pin 4  → Relay IN
ESP32 Pin 23 → DS18B20 Data (with 4.7kΩ pullup to 3.3V)
ESP32 GND    → DS18B20 GND
ESP32 3V3    → DS18B20 VCC (via pullup)

ESP32 Pin 2  → Status LED (via 220Ω resistor to GND)
```

## Required Libraries

Install via Arduino IDE: **Library Manager**

1. **PubSubClient** (v2.8.0+)
   - MQTT client support
   - `Sketch → Include Library → Manage Libraries → Search "pubsubclient"`

2. **ArduinoJson** (v6.19.0+)
   - JSON parsing for MQTT messages
   - `Search "ArduinoJson" in Library Manager`

3. **DallasTemperature** (v3.9.0+)
   - OneWire temperature sensor library
   - `Search "DallasTemperature"`

4. **OneWire** (v2.3.5+)
   - OneWire protocol
   - `Search "OneWire"`

**Note:** WiFi and Preferences are built-in to ESP32 core. No additional installation needed.

## Installation & Setup

### 1. Install ESP32 Board Support

In Arduino IDE:
- Open **File → Preferences**
- Add to "Additional Boards Manager URLs": 
  ```
  https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
  ```
- Open **Tools → Board → Boards Manager**
- Search "ESP32" → Install **esp32 by Espressif Systems**

### 2. Configure Arduino IDE

- **Board:** ESP32 Dev Module (or your specific variant)
- **Flash Size:** 4MB
- **Partition Scheme:** Default (1.3MB APP / 1.3MB SPIFFS)
- **CPU Frequency:** 240 MHz
- **Flash Frequency:** 80 MHz
- **Flash Mode:** DIO
- **Port:** `/dev/ttyUSB0` (Linux/Mac) or `COM*` (Windows)
- **Upload Speed:** 921600 baud

### 3. Update Configuration

Edit these values in `tankctl_esp32.ino`:

```cpp
#define WIFI_SSID "EMPIRE"
#define WIFI_PASSWORD "30379718"
#define MQTT_SERVER "192.168.1.100"
#define DEFAULT_TANK_ID "tank1"
```

### 4. Upload Firmware

```bash
# Using Arduino IDE:
1. Connect ESP32 via USB
2. Click Upload (arrow button)
3. Wait for "Leaving... Hard resetting via RTS pin"
```

**If upload fails:** Hold **BOOT button** during upload.

## Features

✅ **Reliable WiFi** - Better range and stability than UNO R4
✅ **Dual-core capable** - Can run background tasks on second core
✅ **NVS Storage** - Persistent configuration storage (up to 16MB)
✅ **Deep Sleep** - Reduce power consumption (optional)
✅ **Temperature Telemetry** - DS18B20 sensor support
✅ **Scheduled Relay Control** - Turn pump on/off at specific times
✅ **MQTT Command Support** - Remote control via MQTT
✅ **Status LED** - Visual feedback for WiFi/MQTT connection
✅ **Automatic NTP Sync** - Accurate timekeeping
✅ **Heap Monitoring** - Tracks free memory in heartbeat

## Firmware Behavior

### Telemetry (every 10 seconds)
Publishes temperature reading to: `tankctl/{tank_id}/telemetry`

### Heartbeat (every 30 seconds)
Includes: WiFi signal strength, uptime, free heap, firmware version

### Command Topics
Listen on: `tankctl/{tank_id}/command`

Supported commands:
- `{"command":"set_light","value":"on","version":1}`
- `{"command":"set_schedule","on_time":"18:00","off_time":"06:00","version":2}`
- `{"command":"reboot_device","version":3}`

### Configuration Storage (NVS)
- `tank_id` - Device identifier
- `sched_on_h`, `sched_on_m` - Schedule on time
- `sched_off_h`, `sched_off_m` - Schedule off time
- `sched_enabled` - Enable/disable scheduling

## Debug Serial Output

```bash
# Connect to serial monitor:
# Linux: screen /dev/ttyUSB0 115200
# Or use Arduino IDE Serial Monitor (115200 baud)
```

Expected output:
```
=== TankCtl ESP32 Device Starting ===

Connecting to WiFi: EMPIRE
WiFi connected. IP: 192.168.1.50

Connecting to MQTT broker: 192.168.1.100:1883
MQTT connected
Subscribed to: tankctl/tank1/command

Telemetry: temp=24.5°C
Heartbeat sent
Schedule: 18:0 - 6:0 (enabled)
```

## Optimization Tips

1. **Power Saving:** Enable sleep mode between measurements
2. **WiFi:** Use fixed IP + DNS caching for faster reconnects
3. **MQTT:** Reduce QoS level if network unstable (currently QoS 1)
4. **Heap:** Monitor `free_heap` in heartbeat logs
5. **OTA Updates:** ESP32 supports firmware updates over WiFi

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Won't upload | Press BOOT button during upload; check COM port |
| WiFi disconnects | Reduce distance to router; check SSID/password |
| MQTT not connecting | Verify broker IP/port in config; check firewall |
| Temperature reads 0 | Check DS18B20 wiring; confirm 4.7kΩ pullup |
| Relay not switching | Verify GPIO 4 logic (active-LOW); check relay wiring |

## Performance Specs

- **Boot Time:** ~2-3 seconds
- **WiFi Connect:** ~2-5 seconds
- **MQTT Connect:** ~1-2 seconds
- **Telemetry Rate:** 10Hz (configurable)
- **Temperature Update:** ~250ms (resolution-dependent)
- **Peak Power:** ~150mA @ max WiFi
- **Idle Power:** ~30-50mA (BLE off)

## Version Info

- **Firmware:** 1.0.0-esp32
- **ESP32 Core:** 2.0.0 or later
- **Tested on:** ESP32 WROOM 32D
- **Compatible with:** ESP32-S3, ESP32-C3 (with pin adjustments)