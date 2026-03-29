---
title: WATER_SCHEDULE_FEATURE
type: note
permalink: tankctl/docs/backend/water-schedule-feature
---

# Water Schedule Feature Documentation

**Last Updated:** Phase 5 (March 2026)  
**Feature Status:** Production-Ready  
**Backend-Side Only:** No firmware changes required

---

## High-Level Overview

The **Water Schedule System** enables users to schedule regular (or one-time) water changes for their devices and receive push notifications at configurable reminder times (24 hours before, 1 hour before, and at the exact time).

### Key Design Characteristics

- **Backend-Driven:** Schedules exist only in the backend database (not synced to device)
- **Timezone-Aware:** Times evaluated in app timezone (default: Asia/Kolkata / IST)
- **FCM-Based Delivery:** Reminders sent via Firebase Cloud Messaging, not MQTT
- **No Device Firmware Needed:** Works with all existing device hardware (ESP32, Arduino UNO R4 WiFi)
- **Flexible Scheduling:** Weekly recurring or one-time custom dates
- **User-Controlled Reminders:** Individual notification preference flags per schedule

### Features at a Glance

✅ Create weekly recurring water change schedules (e.g., Monday/Wednesday/Friday at noon)  
✅ Create custom one-time water change schedules (e.g., Feb 28, 2025 at 2:30 PM)  
✅ Independent notification preferences: 24h warning, 1h warning, on-time alert  
✅ Update or delete schedules anytime  
✅ View all schedules for a device  
✅ Backend-driven evaluation with in-memory duplicate prevention  
✅ Full timezone support (evaluated in configured app timezone)  

---

## Database Schema

### WaterScheduleModel

```python
class WaterScheduleModel(Base):
    """Water change schedule record (backend-only, not synced to device)"""
    
    __tablename__ = "water_schedules"
    
    id: int = Column(Integer, primary_key=True)
    device_id: str = Column(String, ForeignKey("devices.device_id"), nullable=False)
    
    # Schedule Type
    schedule_type: Literal["weekly", "custom"] = Column(String, nullable=False)
    days_of_week: str = Column(String, nullable=True)  # For weekly: "1,3,5" (comma-separated)
    schedule_date: date = Column(Date, nullable=True)   # For custom: specific date
    schedule_time: time = Column(Time, nullable=False)  # HH:MM in app timezone
    
    # User Content
    notes: str = Column(String, nullable=True)  # Optional user notes
    
    # Status & Control
    enabled: bool = Column(Boolean, default=True)  # Enable/disable schedule
    completed: bool = Column(Boolean, default=False)  # Marked as completed (manual)
    
    # Notification Preferences (Phase 2)
    notify_24h: bool = Column(Boolean, default=True)  # Reminder 24 hours before
    notify_1h: bool = Column(Boolean, default=True)   # Reminder 1 hour before
    notify_on_time: bool = Column(Boolean, default=True)  # Reminder at exact time
    
    # Timestamps
    created_at: datetime = Column(DateTime(timezone=True), server_default=utcnow())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=utcnow())
```

### Migration Reference

See `migrations/008_add_days_of_week_multiple.sql` and related migrations for schema evolution and notification preference columns (`notify_24h`, `notify_1h`, `notify_on_time`).

---

## API Reference

### Create Water Schedule

```http
POST /devices/{device_id}/water-schedules
Content-Type: application/json

{
  "schedule_type": "weekly",
  "days_of_week": [1, 3, 5],
  "schedule_time": "12:00",
  "notes": "Regular Friday water change",
  "enabled": true,
  "notify_24h": true,
  "notify_1h": true,
  "notify_on_time": true
}
```

**Response (201):**
```json
{
  "id": 42,
  "device_id": "tank1",
  "schedule_type": "weekly",
  "days_of_week": [1, 3, 5],
  "schedule_date": null,
  "schedule_time": "12:00",
  "notes": "Regular Friday water change",
  "completed": false,
  "enabled": true,
  "notify_24h": true,
  "notify_1h": true,
  "notify_on_time": true,
  "created_at": "2025-01-15T10:00:00+05:30",
  "updated_at": "2025-01-15T10:00:00+05:30"
}
```

### Update Water Schedule

```http
PUT /devices/{device_id}/water-schedules/{schedule_id}
Content-Type: application/json

{
  "schedule_time": "14:00",
  "notify_1h": false
}
```

**Supports partial updates** — send only fields you want to change.

### List Water Schedules

```http
GET /devices/{device_id}/water-schedules

Response: array[WaterScheduleResponse]
```

### Delete Water Schedule

```http
DELETE /devices/{device_id}/water-schedules/{schedule_id}

Response: 204 No Content
```

---

## Notification System

### Reminder Evaluation Pipeline

```
┌─ APScheduler (background job, every 1 minute)
│
├─ Query: Get all active water schedules
│
├─ For each schedule:
│  │
│  ├─ WaterScheduleReminderService.get_due_reminders()
│  │  ├─ Evaluate: Is current time 24h before?
│  │  ├─ Evaluate: Is current time 1h before?
│  │  ├─ Evaluate: Is current time at exact time?
│  │  ├─ Filter: Check notification preferences (notify_24h, notify_1h, notify_on_time)
│  │  ├─ Check: Already sent within 2-hour window? (sent-cache)
│  │  └─ Return: list[(schedule, reminder_type)]
│  │
│  └─ For each due reminder:
│     │
│     ├─ Fetch device's FCM tokens
│     ├─ Format notification message
│     ├─ Send via Firebase Cloud Messaging
│     └─ Add to sent-cache
│
└─ Repeat every 60 seconds
```

### Notification Messages

| Reminder Type | Title | Body |
|---|---|---|
| **24-Hour** | 💧 Water Change Tomorrow — {label} | Water change for {label} is scheduled for tomorrow at {time}. Prepare your supplies. |
| **1-Hour** | 💧 Water Change in 1 Hour — {label} | Water change for {label} starts in 1 hour at {time}. Time to get ready. |
| **On-Time** | 🪣 Time to Change Water — {label} | Your scheduled water change for {label} is due now at {time}. |

### Duplicate Prevention (In-Memory Sent-Cache)

**Problem:** If scheduler restarts or runs late, same reminder might be sent twice.

**Solution:** In-memory cache with 2-hour TTL:
```python
cache_key = (schedule_id, reminder_type, iso_date_str)
# Example: (42, "day_before", "2025-01-15")
```

- Cache lost on process restart (acceptable — at worst, one extra notification)
- TTL is 2 hours (reminder firing window guaranteed < 2 hours)
- Prevents duplicate notifications within a single day for same schedule

### Prerequisites

- Device must have **registered FCM push token** via mobile app
- Backend must have **Firebase Cloud Messaging credentials** (`FCM_PROJECT_ID`, service account JSON)
- Device must have **mobile app installed** to receive notifications

---

## Timezone Handling

### Wall-Clock Time Approach

All schedule times are stored as wall-clock times **without explicit timezone info** in the database:

```python
schedule_time = time(12, 0)  # Noon (no timezone)
schedule_date = date(2025, 2, 15)  # No timezone
```

**Evaluation Rule:** Times are treated as times in the **configured app timezone** (default: `Asia/Kolkata` / IST).

### Example

```python
# config/settings.py
APP_TIMEZONE = "Asia/Kolkata"  # IST (UTC+5:30)

# Schedule created with time = 12:00 (stored as time(12, 0))
# When backend evaluates: now = datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata"))
# If now.time() ~= 12:00, reminder fires
```

### Side Effects

- Daylight saving time (DST): Not applicable in IST (no DST)
- Timezone changes: If app timezone config changes, existing schedules re-evaluated against new timezone
- User in different timezone: User sees times in app timezone, not their local timezone
  - Example: User in EST might see "12:00" but it's actually 10:30 PM in their time

### Future Improvement

Store explicit timezone or user timezone preference to display times correctly in mobile app UI.

---

## Service Layer

### DeviceService Methods

```python
def create_water_schedule(self, device_id: str, schedule_data: dict) -> WaterScheduleModel
    """Create new water schedule. Returns created schedule object."""

def get_water_schedules(self, device_id: str) -> list[WaterScheduleModel]
    """Get all water schedules for device."""

def update_water_schedule(self, device_id: str, schedule_id: int, schedule_data: dict) -> WaterScheduleModel
    """Update schedule (partial or full). Returns updated schedule."""

def delete_water_schedule(self, device_id: str, schedule_id: int) -> bool
    """Delete schedule. Returns True if deleted."""
```

### WaterScheduleReminderService

```python
class WaterScheduleReminderService:
    """Determines which water schedule reminders should fire at current time."""
    
    def get_due_reminders(self, schedules: list[WaterScheduleModel]) 
        -> list[tuple[WaterScheduleModel, str]]:
        """
        Return (schedule, reminder_type) pairs that should fire right now.
        Filters by notification preferences (notify_24h, notify_1h, notify_on_time).
        """
        # Evaluates all schedules against current time (app timezone)
        # Returns list of reminders due (filtered by preferences)
```

### Integration with APScheduler

```python
# In main.py or infrastructure/scheduler/scheduler.py

async def water_schedule_reminder_job():
    """Check if any water schedule reminders need to be sent."""
    schedules = device_service.get_all_water_schedules()
    
    due_reminders = reminder_service.get_due_reminders(schedules)
    
    for schedule, reminder_type in due_reminders:
        notification = format_notification(schedule, reminder_type)
        push_service.send_notification(
            device_id=schedule.device_id,
            title=notification['title'],
            body=notification['body']
        )

# Register job
scheduler.add_job(
    water_schedule_reminder_job,
    'interval',
    minutes=1,
    id='water_schedule_reminders'
)
```

---

## Data Model Diagram

```
┌──────────────────────────────────────────────┐
│              Device                           │
│  (device_id, status, firmware_version, ...)  │
└───────────────────┬──────────────────────────┘
                    │ 1:N
                    │
┌───────────────────▼──────────────────────────┐
│         WaterScheduleModel                    │
│  ┌───────────────────────────────────────┐   │
│  │ id                                    │   │
│  │ device_id (FK)                        │   │
│  │ schedule_type ("weekly"|"custom")     │   │
│  │ days_of_week ("1,3,5") [weekly only]  │   │
│  │ schedule_date (2025-02-15) [custom]   │   │
│  │ schedule_time (12:00)                 │   │
│  │ notes                                 │   │
│  │ enabled (bool)                        │   │
│  │ completed (bool)                      │   │
│  ├─ NOTIFICATION PREFERENCES ──────────┤   │
│  │ notify_24h (bool, default=True)       │   │
│  │ notify_1h (bool, default=True)        │   │
│  │ notify_on_time (bool, default=True)   │   │
│  │ created_at, updated_at                │   │
│  └───────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

---

## Testing

### Unit Tests

See `tests/test_water_schedule_reminders.py` for comprehensive reminder evaluation tests:

```python
def test_weekly_schedule_fires_on_day():
    """Weekly schedule fires on matching day of week"""

def test_reminder_filters_by_notify_24h():
    """24-hour reminder respects notify_24h preference"""

def test_reminder_filters_by_notify_1h():
    """1-hour reminder respects notify_1h preference"""

def test_reminder_filters_by_notify_on_time():
    """On-time reminder respects notify_on_time preference"""

def test_duplicate_prevention_within_2_hours():
    """Same reminder not sent twice within 2-hour window"""

def test_custom_schedule_fires_on_date():
    """Custom schedule fires on specified date"""
```

### Integration Tests

Manual test scenarios:
1. Create weekly schedule → verify GET returns it
2. Update schedule time → verify PUT reflected
3. Set `notify_1h=False` → verify 1-hour reminder doesn't fire
4. Delete schedule → verify DELETE removes it
5. Check FCM logs → verify push notifications sent at correct times

---

## Known Limitations & Future Enhancements

### Current Limitations

- ⚠️ **Timezone-Naive UI:** App shows times in server timezone, not user's local timezone
- ⚠️ **No Timezone Per-User:** All users see times in `APP_TIMEZONE` (IST by default)
- ⚠️ **Single Notification Time:** Can't customize reminder times (fixed at 24h, 1h, on-time)
- ⚠️ **No Schedule Recurring Patterns:** Only weekly or custom date (no bi-weekly, monthly, etc.)
- ⚠️ **Manual Completion:** No auto-marking of schedule as "completed" (user must manually close reminder)

### Potential Enhancements

1. **Per-User Timezone Preference**
   - Store user's timezone in profile
   - Display schedule times in user's local timezone
   - Evaluate reminders in user's timezone

2. **Smart Scheduling**
   - ML-based reminder suggestions ("You usually change water on Saturdays")
   - Habits-based recommendations

3. **Recurring Pattern Library**
   - Bi-weekly, monthly, quarterly schedules
   - "Every N weeks" pattern

4. **Custom Reminder Times**
   - Allow users to set different reminder offsets (e.g., 48h, 12h before)
   - Multiple reminders per day

5. **Completion Tracking**
   - Auto-mark schedule as completed after water change (check device's last maintenance command)
   - Track completion rate → show stats in app

6. **Family Sharing**
   - Assign schedule to family member's name
   - Track who completed water change

---

## Consistency & Validation

### Notification Preference Defaults

All notification preferences default to `True` for backward compatibility and maximum user engagement.

**Defaults:**
```json
{
  "notify_24h": true,
  "notify_1h": true,
  "notify_on_time": true,
  "enabled": true
}
```

### Schema Validation

**WaterScheduleRequest:**
- `schedule_type` required, must be "weekly" or "custom"
- For weekly: `days_of_week` required, must be list of int 0-6
- For custom: `schedule_date` required, must be YYYY-MM-DD format
- `schedule_time` required, must be HH:MM format
- Notification preferences must be boolean

**Example validation error:**
```json
{
  "detail": "schedule_type='weekly' requires days_of_week"
}
```

---

## Cross-Reference Documentation

For more details, see:

- **API Endpoints:** [docs/backend/commands/commands.md](commands/commands.md) (Water Schedule Endpoints section)
- **Architecture:** [docs/backend/architecture/architecture.md](architecture/architecture.md) (Water Schedule Service Architecture)
- **Device Support:** [docs/device_firmware/firmware/DEVICES.md](../../device_firmware/firmware/DEVICES.md) (Water Schedule System section)
- **Notification System:** [backend/PHASE2_NOTIFICATION_PREFERENCES.md](PHASE2_NOTIFICATION_PREFERENCES.md)
- **Implementation:** `src/services/water_schedule_reminder_service.py`, `src/services/device_service.py`
- **Tests:** `tests/test_water_schedule_*.py`

---

## Change Log

| Phase | Date | Changes |
|---|---|---|
| Phase 1 | Jan 2025 | Initial water schedule endpoints (POST, GET, DELETE) |
| Phase 2 | Feb 2025 | Notification preferences (notify_24h, notify_1h, notify_on_time) |
| Phase 4 | Mar 2025 | PUT endpoint for partial updates, reminder service maturity |
| Phase 5 | Mar 2026 | Documentation automation, full API documentation, architecture sync |