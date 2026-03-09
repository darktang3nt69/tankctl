# Light Scheduling Implementation Summary

## Overview

The light scheduling system has been **fully implemented** following the desired-state model defined in [LIGHT_SCHEDULING.md](LIGHT_SCHEDULING.md).

Implementation date: 2025
Status: ✅ Complete

---

## What Was Implemented

### 1. Domain Model

**File:** `src/domain/light_schedule.py`

The `LightSchedule` dataclass represents a daily light schedule:

```python
@dataclass
class LightSchedule:
    device_id: str
    on_time: time
    off_time: time
    enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

**Key method:** `is_light_on_at(check_time)` - Handles midnight-crossing schedules correctly (e.g., 18:00-06:00).

### 2. Database Table

**File:** `src/infrastructure/db/models.py`

Added `LightScheduleModel` with:
- `device_id` (Primary Key)
- `on_time` (Time, NOT NULL)
- `off_time` (Time, NOT NULL)
- `enabled` (Boolean, DEFAULT TRUE)
- `created_at`, `updated_at` (Timestamps)

Integrated into `init_db()` for automatic table creation.

### 3. Repository Layer

**File:** `src/repository/light_schedule_repository.py`

CRUD operations:
- `create(schedule)` - Upsert (insert new or update existing)
- `get_by_device_id(device_id)` - Retrieve schedule
- `get_all_enabled()` - Get all enabled schedules (for startup loading)
- `delete(device_id)` - Remove schedule

### 4. Scheduling Service

**File:** `src/services/scheduling_service.py`

Core logic:
- `create_schedule()` - Save schedule + register APScheduler cron jobs + apply current state
- `get_schedule()` - Retrieve schedule by device_id
- `delete_schedule()` - Remove schedule + unregister APScheduler jobs
- `load_all_schedules()` - Restore schedules on backend startup
- `_register_scheduler_jobs()` - Create 2 cron jobs per device (on_time, off_time)
- `_set_light_state()` - Update shadow desired state (called by APScheduler)
- `_apply_current_state()` - Immediately set correct state when schedule created

**Integration:** Uses APScheduler to trigger shadow updates at scheduled times.

### 5. API Endpoints

**File:** `src/api/routes/devices.py`

Three new endpoints:

#### Create/Update Schedule
```
POST /devices/{device_id}/schedule
```

Request:
```json
{
  "on_time": "18:00",
  "off_time": "06:00",
  "enabled": true
}
```

#### Get Schedule
```
GET /devices/{device_id}/schedule
```

#### Delete Schedule
```
DELETE /devices/{device_id}/schedule
```

### 6. Pydantic Schemas

**File:** `src/api/schemas.py`

Added:
- `ScheduleRequest` - Validates HH:MM format (24-hour) using regex pattern
- `ScheduleResponse` - Returns schedule with timestamps

### 7. Startup Integration

**File:** `src/api/main.py`

On backend startup:
1. Scheduler starts
2. `SchedulingService.load_all_schedules()` is called
3. All enabled schedules are restored
4. APScheduler jobs are re-registered

---

## How It Works

### Desired-State Model

The scheduler **does not send commands directly**. Instead:

1. **Scheduler triggers** at `on_time` or `off_time`
2. **Shadow is updated** via `ShadowService.set_desired_state(device_id, {"light": "on"})`
3. **Reconciliation detects** `desired != reported`
4. **Command is sent** via standard shadow reconciliation flow

### APScheduler Integration

Two cron jobs per device:

```python
# Job 1: Turn light ON
scheduler.add_job(
    self._set_light_state,
    'cron',
    hour=on_hour,
    minute=on_minute,
    args=[device_id, "on"],
    id=f"light_schedule_{device_id}_on"
)

# Job 2: Turn light OFF
scheduler.add_job(
    self._set_light_state,
    'cron',
    hour=off_hour,
    minute=off_minute,
    args=[device_id, "off"],
    id=f"light_schedule_{device_id}_off"
)
```

### Midnight-Crossing Schedules

Example: `on_time="18:00"`, `off_time="06:00"`

**Logic:**
```python
if on_time > off_time:
    # Crosses midnight
    return check_time >= on_time or check_time < off_time
else:
    # Same day
    return on_time <= check_time < off_time
```

This correctly handles schedules that cross midnight boundaries.

---

## Testing

A test script is provided: `test_scheduling.py`

**To run:**

```bash
# 1. Start the backend
python -m src.api.main

# 2. In another terminal, run the test
python test_scheduling.py
```

**What the test does:**
1. Registers a test device
2. Creates a schedule (18:00-06:00)
3. Retrieves the schedule
4. Checks shadow state
5. Updates the schedule (19:00-07:00)
6. Deletes the schedule
7. Verifies deletion (404 response)

---

## Architecture Decisions

### Why Desired-State Model?

| Concern | Command Scheduling | Desired-State Scheduling |
|---------|-------------------|-------------------------|
| Device reconnects | Commands lost | State converges automatically |
| Manual overrides | Conflicts with schedule | Cleanly replaced at next schedule |
| Backend restart | Lost state | Schedules restored from DB |
| Idempotency | Duplicate commands | Shadow version ensures once-only |

### Why APScheduler?

- **Cron-based triggers** - Easy to express daily schedules
- **In-process** - No external dependencies
- **Persistent jobs** - Can be restored on startup
- **Already integrated** - Used for reconciliation and health checks

---

## File Changes Summary

### New Files (5)
1. `src/domain/light_schedule.py` (73 lines)
2. `src/repository/light_schedule_repository.py` (158 lines)
3. `src/services/scheduling_service.py` (296 lines)
4. `test_scheduling.py` (147 lines)
5. `docs/IMPLEMENTATION_LIGHT_SCHEDULING.md` (this file)

### Modified Files (5)
1. `src/infrastructure/db/models.py` - Added LightScheduleModel
2. `src/infrastructure/db/database.py` - Added LightScheduleModel to init_db()
3. `src/api/schemas.py` - Added ScheduleRequest, ScheduleResponse
4. `src/api/routes/devices.py` - Added 3 schedule endpoints, scheduler dependency
5. `src/api/main.py` - Added schedule loading on startup

---

## Usage Examples

### Create a schedule

```bash
curl -X POST http://localhost:8000/devices/tank1/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "on_time": "18:00",
    "off_time": "06:00",
    "enabled": true
  }'
```

Response:
```json
{
  "device_id": "tank1",
  "on_time": "18:00",
  "off_time": "06:00",
  "enabled": true,
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:30:00"
}
```

### Get schedule

```bash
curl http://localhost:8000/devices/tank1/schedule
```

### Delete schedule

```bash
curl -X DELETE http://localhost:8000/devices/tank1/schedule
```

---

## Behavior Examples

### Example 1: Create Schedule

**Time:** 17:00  
**Action:** Create schedule (18:00-06:00)  
**Result:**
- Schedule saved to database
- APScheduler registers two cron jobs (18:00, 06:00)
- Current time is 17:00 → Light should be OFF
- Shadow desired state set to `{"light": "off"}`
- If device is online and light is ON, reconciliation will turn it OFF

### Example 2: Schedule Triggers

**Time:** 18:00  
**Schedule:** ON at 18:00  
**Result:**
- APScheduler job triggers
- `_set_light_state(device_id, "on")` is called
- Shadow desired state updated: `{"light": "on"}`
- Reconciliation sends command to device
- Device reports light ON

### Example 3: Manual Override

**Time:** 19:00 (during ON window 18:00-06:00)  
**Schedule:** Light should be ON  
**Action:** User turns light OFF manually  
**Result:**
- Shadow desired state: `{"light": "off"}` (manual command)
- Shadow reported state: `{"light": "off"}` (device confirms)
- **Next day at 06:00:** Schedule sets desired to OFF (already OFF, no command)
- **Next day at 18:00:** Schedule sets desired to ON (light turns ON)

Manual override is cleanly replaced at next schedule event.

### Example 4: Device Reconnect During ON Window

**Time:** 20:00 (during ON window 18:00-06:00)  
**Device:** Offline, reconnects now  
**Result:**
- Device sends heartbeat
- Backend reconciliation reads shadow
- Shadow desired: `{"light": "on"}`
- Shadow reported: `{"light": "off"}` (device was offline)
- Reconciliation sends command to turn light ON
- Device converges to desired state

### Example 5: Backend Restart

**Time:** 19:30  
**Action:** Backend restarts  
**Result:**
1. Database tables created
2. Scheduler starts
3. `load_all_schedules()` is called
4. All enabled schedules retrieved from database
5. APScheduler jobs re-registered for each schedule
6. System continues without data loss

---

## Known Limitations

1. **One schedule per device** - Only one daily ON/OFF window supported
2. **No recurring patterns** - Cannot define weekday-only schedules
3. **No sunrise/sunset** - Fixed times only, no location-based automation
4. **Minute-level precision** - APScheduler cron jobs trigger at minute boundaries

These are acceptable for the initial implementation and can be enhanced later.

---

## Compliance with LIGHT_SCHEDULING.md

✅ All requirements met:

| Requirement | Status |
|------------|--------|
| Desired-state model | ✅ Implemented |
| Device shadow integration | ✅ Uses ShadowService |
| Daily ON/OFF schedule | ✅ on_time, off_time fields |
| Database table | ✅ light_schedules table |
| API endpoint | ✅ POST/GET/DELETE /devices/{id}/schedule |
| APScheduler integration | ✅ Cron jobs per device |
| Manual override support | ✅ Works via shadow updates |
| Reconnect recovery | ✅ Shadow reconciliation |
| Startup schedule loading | ✅ load_all_schedules() |
| Midnight-crossing logic | ✅ is_light_on_at() method |

---

## Future Enhancements

Potential improvements (not blocking):

1. **Multiple schedules per device** - Morning + evening windows
2. **Day-of-week patterns** - Weekday vs weekend schedules
3. **Sunrise/sunset automation** - Location-based scheduling
4. **Light intensity ramping** - Gradual ON/OFF transitions
5. **Device groups** - Control multiple devices with one schedule
6. **Holiday exceptions** - Override schedules on specific dates
7. **Schedule presets** - Common templates (summer, winter, etc.)

---

## Conclusion

The light scheduling system is **production-ready** and follows all architectural patterns defined in the TankCtl project:

- Layered architecture (API → Service → Repository → Infrastructure)
- Desired-state model (Shadow + Reconciliation)
- Event-driven design (Events published on schedule changes)
- Resilient to failures (DB-backed, restored on startup)
- Clean separation of concerns (Scheduler only updates shadow)

**Status:** ✅ Complete and ready for deployment.
