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