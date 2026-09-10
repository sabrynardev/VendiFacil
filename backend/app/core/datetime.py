from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import get_settings


def business_timezone() -> ZoneInfo:
    try:
        return ZoneInfo(get_settings().business_timezone)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def local_today() -> date:
    return datetime.now(business_timezone()).date()


def utc_now() -> datetime:
    """Return naive UTC to match the existing SQLAlchemy DateTime columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def local_period_to_utc_bounds(start: date, end: date) -> tuple[datetime, datetime]:
    zone = business_timezone()
    start_at = datetime.combine(start, time.min, tzinfo=zone)
    end_at = datetime.combine(end, time.max, tzinfo=zone)
    return (
        start_at.astimezone(timezone.utc).replace(tzinfo=None),
        end_at.astimezone(timezone.utc).replace(tzinfo=None),
    )


def utc_to_local(value: datetime) -> datetime:
    aware = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    return aware.astimezone(business_timezone())
