"""Timezone helpers for API and scheduling surfaces.

Database values stay UTC; these helpers convert timestamps to configured app timezone
when rendering responses or evaluating wall-clock schedules.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from src.config.settings import settings


def get_app_timezone() -> ZoneInfo:
    """Return configured application timezone."""
    return ZoneInfo(settings.app.timezone)


def now_in_app_timezone() -> datetime:
    """Current datetime in configured app timezone."""
    return datetime.now(get_app_timezone())


def to_app_timezone(dt: datetime) -> datetime:
    """Convert a datetime to configured app timezone.

    Naive datetimes are interpreted as UTC because persistence uses UTC.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(get_app_timezone())


def isoformat_in_app_timezone(dt: datetime | None) -> str | None:
    """Return ISO timestamp in configured app timezone."""
    if dt is None:
        return None
    return to_app_timezone(dt).isoformat()
