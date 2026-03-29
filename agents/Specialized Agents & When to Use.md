---
title: Specialized Agents & When to Use
type: reference
permalink: tankctl/agents/specialized-agents-when-to-use
tags:
- agents
- workflow
- coordination
---

## TankCtl Specialized Agents

### Planning & Orchestration
- **`/planner`** - Research, analyze, and create implementation plans for complex features
- **`/orchestrator`** - Coordinate multi-layer implementations across agents

### Backend Agents
1. **`/backend-core`** 
   - FastAPI + SQLAlchemy + Repository pattern
   - REST endpoints, database models, repositories
   
2. **`/device-communication`**
   - MQTT topics, device shadow, commands
   - Device protocol reliability

3. **`/notifications-and-alerts`**
   - FCM push notifications, alert rules
   - Water scheduling, reminder scheduling

### Device Agents
4. **`/esp32-firmware`**
   - Arduino/C++ embedded code
   - Memory optimization, WiFi/MQTT reliability
   - Device stability and watchdog

### Frontend Agent
5. **`/flutter-foundation`**
   - Riverpod providers, state management
   - Widget/integration tests, GoRouter navigation

### Utilities
- **`/code-cleanup`** - Remove unused code and dead branches
- **`/docs-automation`** - Auto-sync code changes to documentation

### Workflow Example
For adding a new device feature:
1. `/planner` → Create implementation plan
2. `/orchestrator` → Execute plan with agent coordination
3. Or invoke specialized agents directly:
   - `/esp32-firmware` → Device firmware
   - `/backend-core` → API endpoint
   - `/flutter-foundation` → UI implementation
   - `/docs-automation` → Update docs