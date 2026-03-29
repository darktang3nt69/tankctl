# Copilot Instructions

When generating code for this repository:

Follow the architecture defined in:

- docs/ARCHITECTURE.md
- docs/DEVICES.md
- docs/MQTT_TOPICS.md
- docs/COMMANDS.md

Key rules:

- API must not directly access MQTT
- Services contain business logic
- Repository layer handles DB
- MQTT topics must follow tankctl/{device_id}/{channel}

Devices communicate using MQTT and follow DEVICE_PROTOCOL.md.

## Specialized Agents

TankCtl has four **user-invocable specialized agents** that you can explicitly request for deep domain expertise:

### Backend Agents

1. **backend-core** — FastAPI + SQLAlchemy + Repository pattern
   - Use for: REST endpoint design, database models, repository implementations
   - Command: `/backend-core Design a new API endpoint for...`

2. **device-communication** — MQTT + Device Shadow + Commands
   - Use for: MQTT topics, shadow reconciliation, device protocol, firmware
   - Command: `/device-communication Implement device shadow reconciliation for...`

3. **notifications-and-alerts** — FCM + Alerts + Water Scheduling
   - Use for: FCM integration, alert rules, reminder scheduling, notification preferences
   - Command: `/notifications-and-alerts Implement water-low alert thresholds and FCM delivery`

### Frontend Agent

4. **flutter-foundation** — Riverpod + Testing + Navigation + UI
   - Use for: State management, widget testing, navigation, theming, component library
   - Command: `/flutter-foundation Create a Riverpod provider for device telemetry`

## How to Use Agents

- Type `/` in the chat to see available agents
- Select an agent and describe what you need
- Each agent has specialized knowledge for its domain
- Agents understand TankCtl architecture and coordinate across layers

**Example workflow:** When implementing a water alert:
1. `/backend-core` → Design alert service and repository
2. `/notifications-and-alerts` → Implement FCM delivery
3. `/flutter-foundation` → Build alert UI with Riverpod providers

See `agents.md` for detailed patterns and architecture.