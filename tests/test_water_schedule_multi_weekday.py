#!/usr/bin/env python3
"""
Test suite for multi-weekday water schedule reminders.
Tests the new days_of_week functionality (comma-separated string in DB, list in API).

Run with: python tests/test_water_schedule_multi_weekday.py
"""

import sys
from datetime import datetime, date, time as time_type, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, '/mnt/samba/tankctl')

from src.services.water_schedule_reminder_service import WaterScheduleReminderService
from src.config.settings import settings


# Helpers
class MockSchedule:
    """Mock WaterScheduleModel for testing."""
    def __init__(self, id=1, schedule_type='weekly', days_of_week=None,
                 schedule_date=None, schedule_time='12:00',
                 enabled=True, completed=False, device_id='tank1'):
        self.id = id
        self.device_id = device_id
        self.schedule_type = schedule_type
        self.days_of_week = days_of_week  # Comma-separated string: "1,3,5"
        self.schedule_date = schedule_date
        self.schedule_time = time_type(*[int(x) for x in schedule_time.split(':')])
        self.enabled = enabled
        self.completed = completed
        self.notes = "Test schedule"


def assert_due(actual, expected_count, expected_types=None):
    """Helper: assert reminders match expectations."""
    actual_types = [r[1] for r in actual]
    print(f"  Due reminders: {actual_types}")
    assert len(actual) == expected_count, \
        f"Expected {expected_count} reminders, got {len(actual)}: {actual_types}"
    if expected_types:
        for exp_type in expected_types:
            assert exp_type in actual_types, \
                f"Expected reminder type '{exp_type}' not found in {actual_types}"


# Tests
@patch('src.services.water_schedule_reminder_service.now_in_app_timezone')
def test_multi_weekday_monday(mock_now):
    """Test: Multi-weekday schedule fires on Monday (1)."""
    print("\n✓ test_multi_weekday_monday")
    svc = WaterScheduleReminderService()
    tz = ZoneInfo(settings.app.timezone)
    
    # Monday, Wednesday, Friday at 3:00 PM
    schedule = MockSchedule(
        id=1,
        schedule_type='weekly',
        days_of_week='1,3,5',  # Mon, Wed, Fri
        schedule_time='15:00'
    )
    
    # Monday 3:00 PM IST
    now = datetime(2026, 3, 16, 15, 0, 0, tzinfo=tz)  # Monday
    mock_now.return_value = now
    
    due = svc.get_due_reminders([schedule])
    
    assert_due(due, 1, ["on_time"])
    print("  ✓ Fires on Monday at scheduled time")


@patch('src.services.water_schedule_reminder_service.now_in_app_timezone')
def test_multi_weekday_wednesday(mock_now):
    """Test: Multi-weekday schedule fires on Wednesday (3)."""
    print("\n✓ test_multi_weekday_wednesday")
    svc = WaterScheduleReminderService()
    tz = ZoneInfo(settings.app.timezone)
    
    schedule = MockSchedule(
        id=2,
        schedule_type='weekly',
        days_of_week='1,3,5',  # Mon, Wed, Fri
        schedule_time='15:00'
    )
    
    # Wednesday 3:00 PM IST
    now = datetime(2026, 3, 18, 15, 0, 0, tzinfo=tz)  # Wednesday
    mock_now.return_value = now
    
    due = svc.get_due_reminders([schedule])
    
    assert_due(due, 1, ["on_time"])
    print("  ✓ Fires on Wednesday at scheduled time")


@patch('src.services.water_schedule_reminder_service.now_in_app_timezone')
def test_multi_weekday_friday(mock_now):
    """Test: Multi-weekday schedule fires on Friday (5)."""
    print("\n✓ test_multi_weekday_friday")
    svc = WaterScheduleReminderService()
    tz = ZoneInfo(settings.app.timezone)
    
    schedule = MockSchedule(
        id=3,
        schedule_type='weekly',
        days_of_week='1,3,5',  # Mon, Wed, Fri
        schedule_time='15:00'
    )
    
    # Friday 3:00 PM IST
    now = datetime(2026, 3, 20, 15, 0, 0, tzinfo=tz)  # Friday
    mock_now.return_value = now
    
    due = svc.get_due_reminders([schedule])
    
    assert_due(due, 1, ["on_time"])
    print("  ✓ Fires on Friday at scheduled time")


@patch('src.services.water_schedule_reminder_service.now_in_app_timezone')
def test_multi_weekday_skip_tuesday(mock_now):
    """Test: Multi-weekday schedule does NOT fire mid-afternoon on non-scheduled days."""
    print("\n✓ test_multi_weekday_skip_tuesday")
    svc = WaterScheduleReminderService()
    tz = ZoneInfo(settings.app.timezone)
    
    schedule = MockSchedule(
        id=4,
        schedule_type='weekly',
        days_of_week='1,3,5',  # Mon, Wed, Fri
        schedule_time='15:00'  # 3:00 PM is the scheduled time
    )
    
    # Tuesday 2:00 PM (not 3 PM, not 24h before Wed, not 1h before Wed)
    # This is a random time on a non-selected day and not a reminder window
    now = datetime(2026, 3, 17, 14, 0, 0, tzinfo=tz)  # Tuesday 2 PM
    mock_now.return_value = now
    
    due = svc.get_due_reminders([schedule])
    
    assert_due(due, 0)
    print("  ✓ Does NOT fire at random time on non-selected day")


@patch('src.services.water_schedule_reminder_service.now_in_app_timezone')
def test_multi_weekday_hour_before(mock_now):
    """Test: Multi-weekday schedule fires 1 hour before on selected day."""
    print("\n✓ test_multi_weekday_hour_before")
    svc = WaterScheduleReminderService()
    tz = ZoneInfo(settings.app.timezone)
    
    schedule = MockSchedule(
        id=5,
        schedule_type='weekly',
        days_of_week='0,2,4,6',  # Sun, Tue, Thu, Sat
        schedule_time='20:00'  # 8:00 PM
    )
    
    # Thursday 7:00 PM IST (1 hour before)
    now = datetime(2026, 3, 19, 19, 0, 0, tzinfo=tz)  # Thursday
    mock_now.return_value = now
    
    due = svc.get_due_reminders([schedule])
    
    assert_due(due, 1, ["hour_before"])
    print("  ✓ Fires 1 hour before on Thursday")


@patch('src.services.water_schedule_reminder_service.now_in_app_timezone')
def test_multi_weekday_day_before(mock_now):
    """Test: Multi-weekday schedule fires 24 hours before on selected day."""
    print("\n✓ test_multi_weekday_day_before")
    svc = WaterScheduleReminderService()
    tz = ZoneInfo(settings.app.timezone)
    
    schedule = MockSchedule(
        id=6,
        schedule_type='weekly',
        days_of_week='1,4',  # Mon, Thu
        schedule_time='12:00'
    )
    
    # Sunday 12:00 PM IST (24 hours before Monday)
    now = datetime(2026, 3, 15, 12, 0, 0, tzinfo=tz)  # Sunday
    mock_now.return_value = now
    
    due = svc.get_due_reminders([schedule])
    
    assert_due(due, 1, ["day_before"])
    print("  ✓ Fires 24 hours before on Sunday (for Monday)")


@patch('src.services.water_schedule_reminder_service.now_in_app_timezone')
def test_multi_weekday_weekend_only(mock_now):
    """Test: Weekend-only schedule (0,6) fires on Sunday."""
    print("\n✓ test_multi_weekday_weekend_only")
    svc = WaterScheduleReminderService()
    tz = ZoneInfo(settings.app.timezone)
    
    schedule = MockSchedule(
        id=7,
        schedule_type='weekly',
        days_of_week='0,6',  # Sun, Sat
        schedule_time='10:00'
    )
    
    # Sunday 10:00 AM IST
    now = datetime(2026, 3, 15, 10, 0, 0, tzinfo=tz)  # Sunday
    mock_now.return_value = now
    
    due = svc.get_due_reminders([schedule])
    
    assert_due(due, 1, ["on_time"])
    print("  ✓ Weekend-only schedule fires on Sunday")


@patch('src.services.water_schedule_reminder_service.now_in_app_timezone')
def test_multi_weekday_all_tiers_same_day(mock_now):
    """Test: All 3 reminder tiers firing on same day within different time windows."""
    print("\n✓ test_multi_weekday_all_tiers_same_day")
    svc = WaterScheduleReminderService()
    tz = ZoneInfo(settings.app.timezone)
    
    schedule = MockSchedule(
        id=8,
        schedule_type='weekly',
        days_of_week='2',  # Tuesday only
        schedule_time='18:00'  # 6:00 PM
    )
    
    # Test 24h before (Monday 6:00 PM)
    now_24h = datetime(2026, 3, 16, 18, 0, 0, tzinfo=tz)  # Monday
    mock_now.return_value = now_24h
    due_24h = svc.get_due_reminders([schedule])
    assert len(due_24h) == 1 and due_24h[0][1] == "day_before"
    
    # Test 1h before (Tuesday 5:00 PM)
    now_1h = datetime(2026, 3, 17, 17, 0, 0, tzinfo=tz)  # Tuesday
    mock_now.return_value = now_1h
    due_1h = svc.get_due_reminders([schedule])
    assert len(due_1h) == 1 and due_1h[0][1] == "hour_before"
    
    # Test on-time (Tuesday 6:00 PM)
    now_on = datetime(2026, 3, 17, 18, 0, 0, tzinfo=tz)  # Tuesday
    mock_now.return_value = now_on
    due_on = svc.get_due_reminders([schedule])
    assert len(due_on) == 1 and due_on[0][1] == "on_time"
    
    print("  ✓ All 3 tiers fire at correct times (24h before, 1h before, on-time)")


@patch('src.services.water_schedule_reminder_service.now_in_app_timezone')
def test_multi_weekday_empty_list_no_fire(mock_now):
    """Test: Empty days_of_week means schedule never fires."""
    print("\n✓ test_multi_weekday_empty_list_no_fire")
    svc = WaterScheduleReminderService()
    tz = ZoneInfo(settings.app.timezone)
    
    schedule = MockSchedule(
        id=9,
        schedule_type='weekly',
        days_of_week='',  # Empty string (no days selected)
        schedule_time='15:00'
    )
    
    now = datetime(2026, 3, 16, 15, 0, 0, tzinfo=tz)
    mock_now.return_value = now
    
    due = svc.get_due_reminders([schedule])
    
    assert_due(due, 0)
    print("  ✓ Empty days_of_week prevents any reminders")


def main():
    """Run all tests."""
    passed = 0
    failed = 0

    tests = [
        test_multi_weekday_monday,
        test_multi_weekday_wednesday,
        test_multi_weekday_friday,
        test_multi_weekday_skip_tuesday,
        test_multi_weekday_hour_before,
        test_multi_weekday_day_before,
        test_multi_weekday_weekend_only,
        test_multi_weekday_all_tiers_same_day,
        test_multi_weekday_empty_list_no_fire,
    ]

    print("=" * 70)
    print("MULTI-WEEKDAY WATER SCHEDULE REMINDER TESTS")
    print("=" * 70)

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
