from datetime import date, datetime

from app.core.datetime import local_period_to_utc_bounds


def test_bahia_business_day_is_converted_to_utc_bounds():
    start, end = local_period_to_utc_bounds(date(2026, 9, 9), date(2026, 9, 9))

    assert start == datetime(2026, 9, 9, 3, 0, 0)
    assert end == datetime(2026, 9, 10, 2, 59, 59, 999999)
