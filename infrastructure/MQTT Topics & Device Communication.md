---
title: MQTT Topics & Device Communication
type: reference
permalink: tankctl/infrastructure/mqtt-topics-device-communication
tags:
- mqtt
- protocol
- device-communication
---

## MQTT Topics & Messaging Patterns

### Standard Topic Format
```
tankctl/{device_id}/{channel}
```

### Core Topics
- `tankctl/{device_id}/telemetry` - Device sensor readings
- `tankctl/{device_id}/reported` - Device state reports
- `tankctl/{device_id}/command` - Backend → Device commands
- `tankctl/{device_id}/status` - Device status/heartbeat

### Command Format
Commands include version numbers for idempotency:
```json
{
  "command": "set_pump",
  "value": "on",
  "version": 7
}
```

### Device Shadow Model
```
DeviceShadow
├── desired    # What backend wants
├── reported   # What device actually has
└── version    # Version tracking
```

### Key Principles
- Devices ignore commands with older versions
- Reconciliation: if `desired != reported`, publish command
- Version numbers ensure idempotency
- All pub/sub through Mosquitto broker