---
title: MIGRATION
type: note
permalink: tankctl/firmware/esp32/migration
---

# UNO R4 → ESP32 Migration Guide

Quick reference for upgrading from Arduino UNO R4 WiFi to ESP32 WROOM 32D.

## Side-by-Side Comparison

### Libraries Changed

| Feature | UNO R4 | ESP32 |
|---------|--------|-------|
| WiFi | `#include <WiFiS3.h>` | `#include <WiFi.h>` (built-in) |
| LED Matrix | `#include <Arduino_LED_Matrix.h>` | Removed (use GPIO LED instead) |
| Storage | `#include <EEPROM.h>` | `#include <Preferences.h>` (NVS) |
| Time Sync | `NTPClient` library | `configTime()` (built-in) |
| Baud Rate | 9600 | **115200** |

### Pin Configuration

| Function | UNO R4 | ESP32 |
|----------|--------|-------|
| Relay | GPIO 4 | GPIO 4 ✓ |
| Temperature | GPIO 6 | GPIO 23 |
| LED Matrix | Built-in | GPIO 2 (optional LED) |

### Memory & Performance

| Spec | UNO R4 | ESP32 |
|------|--------|-------|
| RAM | 32 KB | 520 KB (+1525%) |
| Flash | 256 KB | 4 MB (+1500%) |
| CPU | 48 MHz | 240 MHz (+400%) |
| WiFi Stability | Fair | Excellent |

## Key Code Changes

### 1. WiFi Connection

**UNO R4:**
```cpp
#include <WiFiS3.h>
WiFiClient wifiClient;
WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
```

**ESP32:**
```cpp
#include <WiFi.h>  // Built-in
WiFiClient wifiClient;
WiFi.mode(WIFI_STA);
WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
```

### 2. Configuration Storage

**UNO R4:**
```cpp
#include <EEPROM.h>

// Save
EEPROM.write(EEPROM_ADDR_TANK_ID + i, tankId[i]);

// Load
char val = EEPROM.read(EEPROM_ADDR_TANK_ID + i);
```

**ESP32:**
```cpp
#include <Preferences.h>

Preferences preferences;
preferences.begin("tankctl", false);

// Save
preferences.putString("tank_id", tankId);

// Load
String savedId = preferences.getString("tank_id", DEFAULT_TANK_ID);
```

### 3. Time Sync

**UNO R4:**
```cpp
#include <NTPClient.h>
#include <WiFiUdp.h>

WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", TIMEZONE_OFFSET_SECONDS);
timeClient.begin();
timeClient.update();

int hour = timeClient.getHours();
```

**ESP32:**
```cpp
#include <time.h>

// No explicit library needed!
configTime(TIMEZONE_OFFSET_SECONDS, 0, "pool.ntp.org", "time.nist.gov");

time_t now = time(nullptr);
struct tm* timeinfo = localtime(&now);
int hour = timeinfo->tm_hour;
```

### 4. LED/Status Indicator

**UNO R4:**
```cpp
#include <Arduino_LED_Matrix.h>

ArduinoLEDMatrix matrix;
matrix.begin();
matrix.renderBitmap(BITMAP, 8, 12);
```

**ESP32:**
```cpp
#define STATUS_LED_PIN 2

pinMode(STATUS_LED_PIN, OUTPUT);
digitalWrite(STATUS_LED_PIN, HIGH);  // On
digitalWrite(STATUS_LED_PIN, LOW);   // Off
```

### 5. Reboot

**UNO R4:**
```cpp
#include <Cortex_M.h>
NVIC_SystemReset();
```

**ESP32:**
```cpp
ESP.restart();
```

## Serial Output Differences

### UNO R4
```
TankCtl Device Starting...
WiFi firmware: 1.2.0
Timezone: Asia/Kolkata (UTC+5:30)
```

### ESP32
```
=== TankCtl ESP32 Device Starting ===

Connecting to WiFi: EMPIRE
WiFi connected. IP: 192.168.1.50
```

Note: ESP32 uses **115200 baud** (vs 9600 on UNO R4).

## Hardware Wiring Comparison

### UNO R4
```
- Relay on Pin 4
- Temp on Pin 6 (OneWire)
- LED Matrix integrated
- Power: 5V
```

### ESP32 WROOM 32D
```
- Relay on GPIO 4 (SAME PIN NUMBER!)
- Temp on GPIO 23 (different physical board location)
- Optional LED on GPIO 2
- Power: 3.3V (NOT 5V!)
```

⚠️ **IMPORTANT:** ESP32 is 3.3V logic. Use level shifters for 5V devices.

## Testing Checklist

- [ ] WiFi connects within 5 seconds
- [ ] MQTT connection established
- [ ] Temperature readings appear every 10s
- [ ] Heartbeat every 30s includes free_heap
- [ ] Relay toggles on command
- [ ] Schedule saves and persists after reboot
- [ ] Serial output at 115200 baud is readable
- [ ] Status LED blinks appropriately

## Common Issues

### Won't Upload
```
esptool.py says: "Timed out waiting for packet header"
→ Hold BOOT button during upload
```

### WiFi Unstable
```
UFI disconnects frequently
→ Move closer to router
→ Check antennas are soldered properly
→ Reduce WIFI_RETRY_INTERVAL_MS if needed
```

### MQTT Won't Connect
```
Connection rc=-2 (Unable to connect)
→ Verify MQTT_SERVER IP is correct
→ Ping from ESP32 to test network
→ Check firewall port 1883
```

### Sensor Reads 0
```
Temperature always 0°C
→ Check GPIO 23 to DS18B20 data pin
→ Verify 4.7kΩ pullup resistor is present
→ Test sensor on known-good UNO R4 first
```

## Power Budget

| State | UNO R4 | ESP32 |
|-------|--------|-------|
| Idle | ~100mA | ~30mA |
| WiFi Tx | ~300mA | ~150mA |
| Peak | ~400mA | ~200mA |

ESP32 is **more power-efficient** despite higher performance.

## Backwards Compatibility

✅ Same MQTT topics
✅ Same command format
✅ Same telemetry structure
✅ Same configuration keys mapped to NVS

**Difference:** Configuration stored in NVS instead of EEPROM, so won't auto-migrate. You'll need to either:
1. Re-enter tank ID on first boot
2. Or manually copy settings from UNO R4's EEPROM

## Why Switch to ESP32?

1. ✅ **Faster WiFi** - 240MHz vs 48MHz
2. ✅ **More memory** - 520KB RAM vs 32KB
3. ✅ **Better stability** - Native WiFi stack vs external module
4. ✅ **Lower cost** - ESP32 boards are $8-15 vs $40+ for UNO R4
5. ✅ **Easy to expand** - Add BLE, SD card, more sensors
6. ✅ **Production-ready** - Used in millions of IoT devices
7. ✅ **Better NTP** - Built-in time sync, no extra library
8. ✅ **Deep sleep** - Wake from GPIO interrupt (future feature)

## Rollback

If you need to revert to UNO R4:
- All NVS data in ESP32 is separate
- UNO R4 EEPROM remains unchanged
- Just reflash original UNO R4 firmware

## Next Steps

1. ✅ Flash ESP32 with `tankctl_esp32.ino`
2. ✅ Connect to WiFi (check Serial at 115200 baud)
3. ✅ Verify MQTT publishes telemetry
4. ✅ Test relay control from app
5. ✅ Deploy in tank monitoring system