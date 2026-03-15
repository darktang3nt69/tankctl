"""Water schedule reminder service.

Evaluates water schedules against current wall-clock time (in the configured
app timezone, default Asia/Kolkata / IST) and returns (schedule, reminder_type)
pairs that should fire right now.

Three reminder tiers per schedule:
    day_before  — 24 h before the event
    hour_before —  1 h before the event
    on_time     —  at exactly the scheduled time

Times are stored in the DB without explicit timezone info and are treated as
wall-clock times in the configured app timezone (APP_TIMEZONE).
"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from src.config.settings import settings
from src.infrastructure.db.models import WaterScheduleModel
from src.utils.logger import get_logger
from src.utils.datetime_utils import now_in_app_timezone

logger = get_logger(__name__)

REMINDER_OFFSETS: dict[str, timedelta] = {
    "day_before": timedelta(hours=24),
    "hour_before": timedelta(hours=1),
    "on_time": timedelta(0),
}

_MESSAGES: dict[str, tuple[str, str]] = {
    "day_before": ("💧 Water Change Tomorrow", "scheduled tomorrow at {time}"),
    "hour_before": ("💧 Water Change in 1 Hour", "starting in 1 hour at {time}"),
    "on_time": ("🪣 Time to Change Water!", "due now at {time}"),
}


class WaterScheduleReminderService:
    """Determines which water schedule reminders should fire at the current time.

    Uses an in-memory sent-cache keyed by (schedule_id, reminder_type, date) to
    prevent the same reminder from firing twice within a 2-hour window.  The cache
    is lost on process restart, which is acceptable — at worst one extra notification
    is sent.
    """

    def __init__(self):
        # key: (schedule_id, reminder_type, iso_date_str) → datetime of last send
        self._sent_cache: dict[tuple[int, str, str], datetime] = {}

    def get_due_reminders(
        self, schedules: list[WaterScheduleModel]
    ) -> list[tuple[WaterScheduleModel, str]]:
        """Return (schedule, reminder_type) pairs that should fire right now."""
        now = now_in_app_timezone()
        due: list[tuple[WaterScheduleModel, str]] = []

        for schedule in schedules:
            if not schedule.enabled or schedule.completed:
                continue
            for reminder_type, offset in REMINDER_OFFSETS.items():
                if self._should_fire(schedule, reminder_type, offset, now):
                    due.append((schedule, reminder_type))

        return due

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _should_fire(
        self,
        schedule: WaterScheduleModel,
        reminder_type: str,
        offset: timedelta,
        now: datetime,
    ) -> bool:
        """Return True if this reminder should fire within the current minute window."""
        target = self._compute_reminder_target(schedule, offset, now)
        if target is None:
            return False

        # Accept if within ±60 s of the target time.
        if abs((now - target).total_seconds()) > 60:
            return False

        # Dedup: don't re-send the same reminder within 2 hours.
        cache_key = (schedule.id, reminder_type, now.date().isoformat())
        last = self._sent_cache.get(cache_key)
        if last and (now - last).total_seconds() < 7200:
            return False

        self._sent_cache[cache_key] = now
        return True

    def _compute_reminder_target(
        self,
        schedule: WaterScheduleModel,
        offset: timedelta,
        now: datetime,
    ) -> datetime | None:
        """Compute when a reminder with the given offset should fire (in app timezone)."""
        tz = ZoneInfo(settings.app.timezone)
        t = schedule.schedule_time  # datetime.time stored without tz info

        if schedule.schedule_type == "custom":
            if not schedule.schedule_date:
                return None
            try:
                event_date = date.fromisoformat(schedule.schedule_date)
            except ValueError:
                return None
            event_dt = datetime(
                event_date.year, event_date.month, event_date.day,
                t.hour, t.minute,
                tzinfo=tz,
            )
            return event_dt - offset

        elif schedule.schedule_type == "weekly":
            if not schedule.days_of_week:
                return None
            
            # Parse comma-separated days_of_week (e.g., "1,3,5" for Mon, Wed, Fri)
            try:
                selected_days = [int(d.strip()) for d in schedule.days_of_week.split(",")]
            except (ValueError, AttributeError):
                return None
            
            # Schema: days_of_week are 0=Sunday … 6=Saturday
            # Python weekday:           0=Monday … 6=Sunday
            # Conversion: py_day = (dow - 1) % 7  (0=Sun→6, 1=Mon→0, …)
            py_selected = [(d - 1) % 7 for d in selected_days]
            
            # Find the next occurrence of any selected day
            current_py_day = now.weekday()
            min_days_ahead = 7  # worst case: wrap around the week
            
            for py_target in py_selected:
                days_ahead = (py_target - current_py_day) % 7
                if days_ahead == 0:
                    # Today is one of the selected days, check if time has passed
                    days_ahead = 0
                min_days_ahead = min(min_days_ahead, days_ahead)
            
            event_date = now.date() + timedelta(days=min_days_ahead)
            event_dt = datetime(
                event_date.year, event_date.month, event_date.day,
                t.hour, t.minute,
                tzinfo=tz,
            )
            return event_dt - offset

        return None

    # ------------------------------------------------------------------
    # Notification text helpers
    # ------------------------------------------------------------------

    def format_time(self, schedule_time) -> str:
        """Format schedule_time as 12-hour AM/PM string."""
        return schedule_time.strftime("%I:%M %p")

    def build_notification(
        self,
        device_name: str | None,
        device_id: str,
        schedule: WaterScheduleModel,
        reminder_type: str,
    ) -> tuple[str, str]:
        """Return (title, body) for the given reminder type."""
        label = device_name or device_id
        time_str = self.format_time(schedule.schedule_time)
        title, body_template = _MESSAGES[reminder_type]
        body = f"{label}: Water change {body_template.format(time=time_str)} IST"
        return title, body
