---
title: Device Firmware Guidelines
type: reference
permalink: tankctl/firmware/device-firmware-guidelines
tags:
- firmware
- arduino
- esp32
- mqtt
---

## Arduino & ESP32 Firmware

### Device Types
- **Arduino UNO R4 WiFi** - Original platform
- **ESP32** - Upgrade path with more memory/features

### MQTT Requirements
Devices MUST:
- **Subscribe to:** `tankctl/{device_id}/command`
- **Publish to:**
  - `tankctl/{device_id}/telemetry` (sensor readings)
  - `tankctl/{device_id}/reported` (state updates)
  - `tankctl/{device_id}/status` (heartbeat)

### Firmware Responsibilities
1. Connect to WiFi and maintain connection
2. Connect to MQTT broker (Mosquitto)
3. Subscribe to command topic
4. Process commands with version checking
5. Publish telemetry at intervals
6. Implement idempotency using version numbers
7. Report temperature, water level, pump status, etc.

### Libraries
- **PubSubClient** - MQTT connectivity
- **ArduinoJson** - JSON parsing
- **WiFi** - Network connectivity (built-in)

### Key Considerations
- Memory constraints (esp32: 520KB SRAM, 4MB Flash)
- WiFi reliability and reconnection logic
- Command versioning for idempotency
- Watchdog for device stability
- Error handling and graceful degradation

### Constraints
- Avoid memory leaks
- Handle WiFi disconnects gracefully
- Implement timeout and retry logic
- Monitor heap for crashes