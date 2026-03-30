---
title: agents
type: note
permalink: tankctl/agents
---

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

TankCtl has a **layered agent system** with planning, coordination, and domain expertise agents. They work together to enforce architecture, plan thoroughly, and implement reliably.

## Planning & Orchestration

### 0. planner (Research + Deep Analysis + Planning)

**When to use:** Complex features, multi-layer changes, uncertain implementations, anything touching multiple layers

**Responsibilities:**
- Research codebase structure and patterns
- Consult auto-generated documentation (ARCHITECTURE.md, COMMANDS.md, MQTT_TOPICS.md, DEVICES.md)
- Map dependencies and identify edge cases
- Create detailed implementation roadmaps with sequencing
- Recommend which specialized agents to invoke and in what order

**How it works:**
```
User: "Add water-level sensor with alerts"
    ↓
Planner: Researches codebase + docs
    ↓ Creates implementation plan with:
    - Layer analysis (firmware, MQTT, API, UI, DB)
    - Dependencies (what must be done first)
    - Risks identified (memory, query perf, alert storms)
    - Recommended agent sequence
    ↓
User: Reviews plan, then invokes orchestrator with plan
    ↓
Orchestrator: Coordinates specialized agents per plan
```

**Example:** `"/planner Add water-level sensor with real-time alerts when water drops below threshold"`

### 1. orchestrator (Multi-Agent Coordination)

**When to use:** Complex multi-step tasks, coordinating across layers, automatic agent sequencing

**Responsibilities:**
- Analyze task complexity and layers involved
- Route to appropriate specialized agents
- Sequence agents based on dependencies
- Integrate results and validate output
- Use planner for complex tasks before executing

**How it works:**
```
Task: Multi-layer feature
    ↓
Orchestrator: Can invoke planner first if complex
    ↓
Planner returns: Implementation plan + agent sequence
    ↓
Orchestrator: Invokes agents in recommended order
    ↓
Result: Implemented, cleaned up, documented
```

**Example:** `"/orchestrator Build a complete pump control feature (firmware, API, UI)"`

---

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

## Documentation Agent

### 6. docs-automation (Auto-Generated Documentation Sync)

**Triggers on:** Changes to `src/api/`, `firmware/`, `src/infrastructure/mqtt/`, `src/domain/`

**Responsibilities:**
- Auto-sync code changes to ARCHITECTURE.md, DEVICES.md, MQTT_TOPICS.md, COMMANDS.md
- Extract API endpoint schemas from Pydantic models
- Extract MQTT topics from PubSubClient subscribe/publish calls
- Extract device commands from Arduino callback functions
- Generate documentation tables and schemas automatically
- Flag orphaned code (documented but not in code) or missing docs (code but no docs)
- Validate cross-references and link integrity

**When active:** You've added new API endpoints, MQTT topics, device commands, or architecture changes and want docs auto-updated to match.

**Example:** `"Auto-generate COMMANDS.md entries for the new pump_control endpoint and MQTT topics"`

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

1. **User-Invocable**: All agents are explicitly invocable via slash commands
   - **Planning**: Type `/planner` to research, analyze, and create implementation plans
   - **Orchestration**: Type `/orchestrator` to coordinate multi-layer implementation
   - **Domain experts**: `/backend-core`, `/device-communication`, `/esp32-firmware`, `/notifications-and-alerts`, `/flutter-foundation`
   - **Utilities**: `/code-cleanup`, `/docs-automation`

2. **Discovery via Descriptions**: Agent descriptions contain trigger phrases and domain keywords
   - Copilot matches your request to the best agent based on description keywords
   - Descriptions include "Use when:" patterns to guide invocation

3. **Cross-References**: Each agent has coordination notes
   - `backend-core` knows about device-communication and notifications-and-alerts
   - `device-communication` knows about esp32-firmware for device-side implementation
   - `esp32-firmware` knows about device-communication for protocol details
   - `flutter-foundation` knows about backend-core
   - **`docs-automation` coordinates with**: backend-core (API schemas), device-communication (MQTT topics), esp32-firmware (command formats)
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

**Scenario: Add a pump control feature with automatic documentation**

1. Define device protocol:
   - Type `/device-communication Design pump command protocol with versioning for idempotency`
   - Result: Command format, MQTT topics defined

2. Build Arduino firmware:
   - Type `/esp32-firmware Implement pump control with safety checks and status reporting`
   - Result: Production Arduino sketch with relay logic

3. Create backend API:
   - Type `/backend-core Design pump control endpoint and device shadow updates`
   - Result: REST API endpoint with validation

4. Build mobile UI:
   - Type `/flutter-foundation Create pump toggle UI with Riverpod command state provider`
   - Result: User-facing pump control interface

5. **Auto-sync documentation**:
   - Type `/orchestrator` automatically invokes `/docs-automation` 
   - **Automatically generates**:
     - COMMANDS.md: Pump control endpoint + payload schema
     - MQTT_TOPICS.md: tankctl/{device_id}/pump_status topic
     - DEVICES.md: Arduino pump handler documentation
     - ARCHITECTURE.md: Pump control data flow diagram
     - Cross-references between all docs

**Result**: Complete feature with end-to-end implementation AND auto-generated, cross-linked documentation.

---

**Scenario: Planning-First Development (Recommended for Complex Features)**

**Goal:** Implement water-level sensor with low-water alerts efficiently

1. **Plan first:**
   ```
   /planner Add water-level sensor with real-time alerts when water drops below threshold
   ```
   - Returns: Detailed plan showing layers, dependencies, edge cases, risks
   - Identifies: Memory constraints (Arduino ADC), database performance (telemetry growth), alert storms
   - Recommends: Specific agent sequence + estimated time

2. **Execute per plan:**
   ```
   /orchestrator [Execute the water-level sensor plan from planner]
   ```
   - Orchestrator runs agents in recommended sequence:
     1. esp32-firmware: ADC reading + smoothing
     2. device-communication: Telemetry topic patterns
     3. backend-core: Alert service + API endpoints
     4. flutter-foundation: Water level gauge UI
     5. code-cleanup: Remove test code
     6. docs-automation: Update all docs

3. **Result:**
   - ✅ Plan prevents mistakes before coding
   - ✅ Clear dependency sequencing (esp32 firmware first, then backend, then UI)
   - ✅ All edge cases identified and mitigated
   - ✅ Estimated time accurate and tracked
   - ✅ Complete end-to-end feature

**When to use Planner:**
- Multi-layer features (touching firmware, API, UI, database)
- Uncertain about where to start (planner provides roadmap)
- Memory-constrained changes (planner identifies limits)
- Integration with existing systems (planner maps connection points)

**When to skip Planner:**
- Single-layer changes (e.g., new API endpoint only)
- Trivial additions (e.g., add a column to UI)
- Quick bug fixes

---

1. Create `.github/agents/your-agent.agent.md`
2. Include `applyTo` patterns for relevant files
3. Add cross-references to related agents
4. Document when to use (trigger phrases in `description`)

Example trigger phrases for discovery:
```
"Use when: doing X, implementing Y, debugging Z"
```

This helps Copilot decide which agent to activate.