---
title: TankCtl Project Overview
type: reference
permalink: tankctl/project/tank-ctl-project-overview
tags:
- overview
- architecture
- project-structure
---

## TankCtl: IoT Water Tank Controller

A self-hosted IoT solution for managing water tank devices with real-time telemetry, alerts, and scheduling.

### Core Technologies
- **Backend:** Python FastAPI + SQLAlchemy + Repository Pattern
- **Frontend:** Flutter (mobile) + Dart
- **IoT Devices:** Arduino UNO R4 WiFi, ESP32
- **Messaging:** MQTT (Mosquitto broker)
- **Cloud:** Firebase Cloud Messaging (FCM) for push notifications
- **Deployment:** Docker + docker-compose
- **Monitoring:** Grafana dashboards

### Project Structure
```
tankctl/
├── src/                 # Python backend
│   ├── api/            # FastAPI routes & schemas
│   ├── services/       # Business logic
│   ├── repository/     # Data access layer
│   ├── domain/         # Pure domain models
│   ├── infrastructure/ # MQTT, DB, scheduler
│   └── config/         # Settings
├── tankctl_app/        # Flutter mobile app
├── firmware/           # Arduino & ESP32 firmware
├── migrations/         # SQL migrations
├── docs/               # Architecture & guides
└── tools/              # Dev scripts & simulators
```

### Architecture Layers
```
API (FastAPI) → Services → Domain → Repository → Infrastructure
```

Key Rules:
- API must NOT directly access MQTT or database
- Services contain business logic
- Repository layer handles DB access
- MQTT topics follow pattern: `tankctl/{device_id}/{channel}`