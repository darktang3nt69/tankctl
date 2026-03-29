# AGENTS.md

## Project

**TankCtl**

TankCtl is a self-hosted IoT controller for managing water tank devices built with:

* Python backend
* MQTT (Mosquitto broker)
* Arduino UNO R4 WiFi devices
* Device Shadow state model

The backend manages device state, commands, and telemetry while devices execute actions and report their status.

---

# Architecture Overview

TankCtl follows a **Layered Architecture**.

```
API → Services → Domain → Repository → Infrastructure
```

### Rules

* API must never talk directly to MQTT or the database
* Business logic belongs in the **service layer**
* Domain models must remain **pure and framework-agnostic**
* Infrastructure handles external systems (MQTT, DB, scheduler)

---

# Project Structure

```
tankctl/
│
├── api/
│   ├── routes/
│   │   ├── device_routes.py
│   │   └── health_routes.py
│   └── schemas.py
│
├── domain/
│   ├── device.py
│   ├── device_shadow.py
│   └── command.py
│
├── services/
│   ├── device_service.py
│   ├── shadow_service.py
│   └── command_service.py
│
├── repository/
│   ├── device_repository.py
│   └── shadow_repository.py
│
├── infrastructure/
│   ├── mqtt/
│   │   ├── mqtt_client.py
│   │   └── mqtt_topics.py
│   │
│   ├── db/
│   │   └── database.py
│   │
│   └── scheduler/
│       └── scheduler.py
│
├── device/
│   └── shadow_reconciler.py
│
├── config/
│   └── settings.py
│
├── utils/
│   └── logger.py
│
├── main.py
└── AGENTS.md
```

---

# Key Concepts

## Device Shadow

Each device has a shadow state.

```
DeviceShadow
 ├─ desired
 ├─ reported
 └─ version
```

Example:

```json
{
  "device_id": "tank1",
  "version": 4,
  "desired": { "pump": "on" },
  "reported": { "pump": "off" }
}
```

The backend reconciles differences between `desired` and `reported`.

---

# MQTT Topics

```
tankctl/{device_id}/telemetry
tankctl/{device_id}/reported
tankctl/{device_id}/command
tankctl/{device_id}/status
```

### Example

```
tankctl/tank1/telemetry
tankctl/tank1/command
```

---

# Command Format

Commands must include a version.

```json
{
  "command": "set_pump",
  "value": "on",
  "version": 7
}
```

Devices must ignore commands with older versions.

---

# Scheduler

APScheduler runs periodic tasks:

```
shadow reconciliation
device heartbeat monitoring
retry failed commands
telemetry cleanup
```

Example reconciliation rule:

```
if desired != reported:
    publish command
```

---

# Coding Guidelines

### Python

* Use type hints
* Prefer dataclasses or pydantic models
* Avoid global state

### Architecture

Never allow:

```
API → MQTT
API → DB
```

Always follow:

```
API → Service → Repository / Infrastructure
```

---

# Logging

Use structured logging.

Example log event:

```
device_id=abc123 event=command_sent command=set_pump
```

---

# Device Firmware Expectations

Devices must:

Subscribe to:

```
tankctl/{device_id}/command
```

Publish to:

```
tankctl/{device_id}/telemetry
tankctl/{device_id}/reported
tankctl/{device_id}/status
```

Devices should implement idempotency using command version numbers.

---

# Design Patterns Used

* Publish–Subscribe
* Device Shadow
* Command Pattern
* Layered Architecture
* Repository Pattern
* Scheduler Pattern

---

# Development Workflow

1. Implement domain models
2. Implement services
3. Implement repositories
4. Implement infrastructure adapters
5. Implement API routes

Never skip layers.

---

# Goals

TankCtl should remain:

* Simple
* Self-hosted
* MQTT-first
* Device-centric
* Reliable even when devices disconnect

---

# Non-Goals

TankCtl is **not** intended to be:

* a full cloud IoT platform
* a distributed microservice system
* a vendor-locked system

It should remain a lightweight device controller.

---

# Specialized Agents

TankCtl has four specialized agents that automatically activate on relevant files. They are **auto-discovered** based on file patterns and work together to enforce architecture and best practices.

## Backend Agents

### 1. backend-core (FastAPI + SQLAlchemy + Repository)

**Triggers on:** `src/api/`, `src/repository/`, `src/infrastructure/db/`, `migrations/`

**Responsibilities:**
- REST API endpoint design with FastAPI
- Database schema design and migrations with SQLAlchemy
- Repository pattern implementation
- Service layer coordination
- Strict enforcement: `API → Service → Repository → DB`

**When active:** You're designing API endpoints, creating database models, or implementing repository methods.

**Example:** `"Design a new REST endpoint for device firmware updates"`

### 2. device-communication (MQTT + Device Shadow + Commands)

**Triggers on:** `src/infrastructure/mqtt/`, `src/domain/device_shadow.py`, `src/services/shadow_service.py`, `firmware/`

**Responsibilities:**
- MQTT topic design and pub/sub patterns
- Device shadow state reconciliation (desired vs reported)
- Command versioning and idempotency
- Device-backend protocol reliability
- Firmware communication patterns

**When active:** You're implementing device protocols, shadow reconciliation, or writing firmware code.

**Example:** `"Implement device shadow reconciliation for light scheduling"`

### 3. notifications-and-alerts (FCM + Alerts + Water Scheduling)

**Triggers on:** `Push notification service`, `alert_service.py`, `water_schedule_reminder_service.py`

**Responsibilities:**
- Firebase Cloud Messaging (FCM) token management
- Alert rule evaluation and thresholds
- Water schedule and recurring reminders
- User notification preferences and quiet hours
- Alert acknowledgment workflows

**When active:** You're implementing push notifications, alert rules, or reminder scheduling.

**Example:** `"Implement water-low alert thresholds and FCM delivery"`

### 4. esp32-firmware (Embedded C++ + Memory Efficiency + Robustness)

**Triggers on:** `firmware/`, `*.ino`, `embedded/`, `esp32/`

**Responsibilities:**
- ESP32 embedded firmware development in Arduino/C++
- Memory optimization (520 KB SRAM, 4 MB Flash constraints)
- Device stability and crash prevention (watchdog, error handling)
- WiFi/MQTT reliability with timeout and reconnection logic
- Power management and real-time constraints
- Health monitoring and diagnostics

**When active:** You're writing or optimizing ESP32 firmware, debugging device crashes, improving memory usage, or handling WiFi/MQTT reliability issues.

**Example:** `"Optimize the ESP32 firmware to prevent memory leaks and handle WiFi disconnects gracefully"`

## Frontend Agent

### 5. flutter-foundation (Riverpod + Testing + Navigation + UI)

**Triggers on:** `tankctl_app/lib/providers/`, `tankctl_app/lib/features/`, `tankctl_app/test/`

**Responsibilities:**
- Riverpod state management and providers
- Widget and integration testing
- GoRouter navigation and deep linking
- Material Design 3 theming with Flex Color Scheme
- MVVM pattern and separation of concerns
- Reusable component library

**When active:** You're building UI features, setting up state management, or writing tests.

**Example:** `"Create a Riverpod provider for device telemetry with caching"`

## Agent Coordination

These agents **automatically coordinate** through file patterns and shared architecture:

```
flutter-foundation (UI Layer)
        ↓ (calls via HTTP)
backend-core (API Layer)
        ↓ (delegates to)
Services
    ├─→ device-communication (MQTT, shadow, commands)
    ├─→ notifications-and-alerts (FCM, alerts, reminders)
    └─→ Repository & Infrastructure
```

### How Agents Work

1. **User-Invocable**: All 5 agents are explicitly invocable via slash commands
   - Type `/backend-core` to request backend infrastructure expertise
   - Type `/device-communication` to request device protocol expertise
   - Type `/esp32-firmware` to request embedded firmware expertise
   - Type `/notifications-and-alerts` to request notification expertise
   - Type `/flutter-foundation` to request Flutter state management expertise

2. **Discovery via Descriptions**: Agent descriptions contain trigger phrases and domain keywords
   - Copilot matches your request to the best agent based on description keywords
   - Descriptions include "Use when:" patterns to guide invocation

3. **Cross-References**: Each agent has coordination notes
   - `backend-core` knows about device-communication and notifications-and-alerts
   - `device-communication` knows about esp32-firmware for device-side implementation
   - `esp32-firmware` knows about device-communication for protocol details
   - `flutter-foundation` knows about backend-core
   - They defer to each other for specialized concerns

### Best Practices for Using Agents

- **Explicit Invocation**: Type `/agent-name` to invoke a specific agent for your task
- **Match Your Task**: Choose the agent whose description best matches what you're doing
- **Leverage Specialization**: Each agent has deep domain expertise—use it!
- **Combine Agents**: For complex multi-layer work, start with one agent then invoke another

### Example Workflow

**Scenario: Add a new device water level alert**

1. Start with backend service design:
   - Type `/backend-core Design a new alert service method for water-low conditions`
   - Backend-core handles service layer architecture

2. Add FCM push notification delivery:
   - Type `/notifications-and-alerts Implement FCM delivery for water-low alert thresholds`
   - notifications-and-alerts handles notification logic

3. Update UI to display alerts:
   - Type `/flutter-foundation Create a Riverpod provider for alert state management`
   - flutter-foundation handles state management and UI coordination

**Result**: Three coordinated layers, each handled by the right specialist agent.

---

**Scenario: Implement reliable device telemetry with WiFi resilience**

1. Define device protocol:
   - Type `/device-communication Design bidirectional telemetry protocol with acknowledged delivery`
   - device-communication handles MQTT topic design and versioning

2. Build robust firmware:
   - Type `/esp32-firmware Implement telemetry collection with WiFi reconnection and memory efficiency`
   - esp32-firmware handles embedded reliability, memory constraints, and watchdog safety

3. Create backend storage:
   - Type `/backend-core Design telemetry repository and aggregation queries`
   - backend-core handles API, database, and telemetry persistence

4. Build monitoring UI:
   - Type `/flutter-foundation Create real-time telemetry charts with Riverpod streaming`
   - flutter-foundation handles UI state management and rendering performance

**Result**: End-to-end telemetry pipeline with embedded robustness, reliable transport, and responsive UI.

---

## Adding New Agents

To create additional specialized agents:

1. Create `.github/agents/your-agent.agent.md`
2. Include `applyTo` patterns for relevant files
3. Add cross-references to related agents
4. Document when to use (trigger phrases in `description`)

Example trigger phrases for discovery:
```
"Use when: doing X, implementing Y, debugging Z"
```

This helps Copilot decide which agent to activate.
