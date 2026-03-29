#!/usr/bin/env python3
"""
Standalone test script for water schedule reminders and backend services.
No external test framework required — uses plain Python assertions.

Run with: python tests/test_water_schedule_reminders_standalone.py
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
    def __init__(self, id=1, schedule_type='weekly', day_of_week=None,
                 schedule_date=None, schedule_time='12:00',
                 enabled=True, completed=False, device_id='tank1'):
        self.id = id
        self.device_id = device_id
        self.schedule_type = schedule_type
        # Convert single day_of_week to days_of_week format
        self.days_of_week = str(day_of_week) if day_of_week is not None else None
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
def test_weekly_schedule_on_time(mock_now):
    """Test: Weekly schedule fires on-time reminder at scheduled time."""
    print("\n✓ test_weekly_schedule_on_time")
    svc = WaterScheduleReminderService()
    tz = ZoneInfo(settings.app.timezone)
    
    # Monday 3:00 PM
    schedule = MockSchedule(
        id=1,
        schedule_type='weekly',
        day_of_week=1,  # Monday
        schedule_time='15:00'
    )
    
    # Monday 3:00 PM IST
    now = datetime(2026, 3, 16, 15, 0, 0, tzinfo=tz)
    mock_now.return_value = now
    
    due = svc.get_due_reminders([schedule])
    
    assert_due(due, 1, ["on_time"])
    print("  ✓ On-time reminder fires at scheduled time")


@patch('src.services.water_schedule_reminder_service.now_in_app_timezone')
def test_weekly_schedule_hour_before(mock_now):
    """Test: Weekly schedule fires 1-hour before reminder."""
    print("\n✓ test_weekly_schedule_hour_before")
    svc = WaterScheduleReminderService()
    tz = ZoneInfo(settings.app.timezone)
    
    schedule = MockSchedule(
        id=2,
        schedule_type='weekly',
        day_of_week=1,  # Monday
        schedule_time='15:00'  # 3:00 PM
    )
    
    # One hour before: Monday 2:00 PM
    now = datetime(2026, 3, 16, 14, 0, 0, tzinfo=tz)
    mock_now.return_value = now
    
    due = svc.get_due_reminders([schedule])
    
    assert_due(due, 1, ["hour_before"])
    print("  ✓ 1-hour before reminder fires")


@patch('src.services.water_schedule_reminder_service.now_in_app_timezone')
def test_weekly_schedule_day_before(mock_now):
    """Test: Weekly schedule fires 24-hour before reminder."""
    print("\n✓ test_weekly_schedule_day_before")
    svc = WaterScheduleReminderService()
    tz = ZoneInfo(settings.app.timezone)
    
    schedule = MockSchedule(
        id=3,
        schedule_type='weekly',
        day_of_week=1,  # Monday
        schedule_time='15:00'  # 3:00 PM
    )
    
    # 24 hours before: Sunday 3:00 PM
    now = datetime(2026, 3, 15, 15, 0, 0, tzinfo=tz)
    mock_now.return_value = now
    
    due = svc.get_due_reminders([schedule])
    
    assert_due(due, 1, ["day_before"])
    print("  ✓ 24-hour before reminder fires")


@patch('src.services.water_schedule_reminder_service.now_in_app_timezone')
def test_wrong_weekday_no_fire(mock_now):
    """Test: Reminder does not fire on wrong day of week."""
    print("\n✓ test_wrong_weekday_no_fire")
    svc = WaterScheduleReminderService()
    tz = ZoneInfo(settings.app.timezone)
    
    schedule = MockSchedule(
        id=4,
        schedule_type='weekly',
        day_of_week=1,  # Monday
        schedule_time='15:00'
    )
    
    # Tuesday 3:00 PM (not Monday)
    now = datetime(2026, 3, 17, 15, 0, 0, tzinfo=tz)
    mock_now.return_value = now
    
    due = svc.get_due_reminders([schedule])
    
    assert_due(due, 0)
    print("  ✓ No reminder on wrong weekday")


@patch('src.services.water_schedule_reminder_service.now_in_app_timezone')
def test_custom_date_on_time(mock_now):
    """Test: Custom date schedule fires on specified date."""
    print("\n✓ test_custom_date_on_time")
    svc = WaterScheduleReminderService()
    tz = ZoneInfo(settings.app.timezone)
    
    schedule = MockSchedule(
        id=5,
        schedule_type='custom',
        schedule_date='2026-03-20',
        schedule_time='10:30'
    )
    
    # March 20, 2026 10:30 AM IST
    now = datetime(2026, 3, 20, 10, 30, 0, tzinfo=tz)
    mock_now.return_value = now
    
    due = svc.get_due_reminders([schedule])
    
    assert_due(due, 1, ["on_time"])
    print("  ✓ On-time reminder fires on custom date")


@patch('src.services.water_schedule_reminder_service.now_in_app_timezone')
def test_custom_date_day_before(mock_now):
    """Test: Custom date schedule fires 24 hours before."""
    print("\n✓ test_custom_date_day_before")
    svc = WaterScheduleReminderService()
    tz = ZoneInfo(settings.app.timezone)
    
    schedule = MockSchedule(
        id=6,
        schedule_type='custom',
        schedule_date='2026-03-20',
        schedule_time='10:30'
    )
    
    # March 19, 2026 10:30 AM (one day before)
    now = datetime(2026, 3, 19, 10, 30, 0, tzinfo=tz)
    mock_now.return_value = now
    
    due = svc.get_due_reminders([schedule])
    
    assert_due(due, 1, ["day_before"])
    print("  ✓ 24-hour before reminder fires on custom date")


@patch('src.utils.datetime_utils.now_in_app_timezone')
def test_disabled_schedule_no_fire(mock_now):
    """Test: Disabled schedule does not trigger reminders."""
    print("\n✓ test_disabled_schedule_no_fire")
    svc = WaterScheduleReminderService()
    tz = ZoneInfo(settings.app.timezone)
    
    schedule = MockSchedule(
        id=7,
        schedule_type='weekly',
        day_of_week=1,
        schedule_time='15:00',
        enabled=False  # DISABLED
    )
    
    now = datetime(2026, 3, 16, 15, 0, 0, tzinfo=tz)
    mock_now.return_value = now
    
    due = svc.get_due_reminders([schedule])
    
    assert_due(due, 0)
    print("  ✓ Disabled schedule does not fire")


@patch('src.utils.datetime_utils.now_in_app_timezone')
def test_completed_schedule_no_fire(mock_now):
    """Test: Completed schedule does not trigger reminders."""
    print("\n✓ test_completed_schedule_no_fire")
    svc = WaterScheduleReminderService()
    tz = ZoneInfo(settings.app.timezone)
    
    schedule = MockSchedule(
        id=8,
        schedule_type='weekly',
        day_of_week=1,
        schedule_time='15:00',
        completed=True  # COMPLETED
    )
    
    now = datetime(2026, 3, 16, 15, 0, 0, tzinfo=tz)
    mock_now.return_value = now
    
    due = svc.get_due_reminders([schedule])
    
    assert_due(due, 0)
    print("  ✓ Completed schedule does not fire")


def test_notification_text_formatting():
    """Test: Notification text generation."""
    print("\n✓ test_notification_text_formatting")
    svc = WaterScheduleReminderService()
    
    schedule = MockSchedule(id=9, schedule_type='weekly', day_of_week=1, schedule_time='15:00')
    
    title, body = svc.build_notification('MyTank', 'tank1', schedule, 'on_time')
    
    print(f"  Title: {title}")
    print(f"  Body: {body}")
    
    assert 'Water' in title or 'water' in body, "Notification should mention water"
    assert 'MyTank' in body, "Notification should include device name"
    assert 'IST' in body, "Notification should mention IST"
    print("  ✓ Notification text includes device, time, and IST")


def test_format_time():
    """Test: Time formatting (12-hour AM/PM)."""
    print("\n✓ test_format_time")
    svc = WaterScheduleReminderService()
    
    # 3:30 PM
    formatted = svc.format_time(time_type(15, 30))
    print(f"  15:30 → {formatted}")
    assert 'PM' in formatted or 'pm' in formatted, "Should include PM"
    assert '3' in formatted or '03' in formatted, "Should include hour"
    
    # 9:15 AM
    formatted = svc.format_time(time_type(9, 15))
    print(f"  09:15 → {formatted}")
    assert 'AM' in formatted or 'am' in formatted, "Should include AM"
    print("  ✓ Time formatting works (12-hour AM/PM)")


def test_timezone_ist():
    """Test: IST timezone is configured."""
    print("\n✓ test_timezone_ist")
    tz_name = settings.app.timezone
    print(f"  Configured timezone: {tz_name}")
    assert 'Kolkata' in tz_name or 'Asia' in tz_name, f"Should be IST timezone, got {tz_name}"
    print("  ✓ IST timezone is properly configured")


# Run all tests
def main():
    """Run all tests."""
    print("=" * 70)
    print("WATER SCHEDULE REMINDER SERVICE TESTS")
    print("=" * 70)
    
    tests = [
        test_weekly_schedule_on_time,
        test_weekly_schedule_hour_before,
        test_weekly_schedule_day_before,
        test_wrong_weekday_no_fire,
        test_custom_date_on_time,
        test_custom_date_day_before,
        test_disabled_schedule_no_fire,
        test_completed_schedule_no_fire,
        test_notification_text_formatting,
        test_format_time,
        test_timezone_ist,
    ]
    
    passed = 0
    failed = 0
    
    for test_fn in tests:
        try:
            test_fn()
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
