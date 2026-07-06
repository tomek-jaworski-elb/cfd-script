"""NYSE trading calendar: full-day holidays and early-close (13:00 ET) sessions.

Built on pandas' holiday framework (pandas is already a dependency) instead of
an exchange-calendar package, to keep the app light. Rules cover the current
NYSE schedule (incl. Juneteenth, observed since 2022); rule changes before that
are out of scope.

Observance quirks encoded here:
- New Year's Day uses sunday_to_monday, not nearest_workday: when Jan 1 falls
  on a Saturday the NYSE stays open the preceding Friday (end of the yearly
  accounting period), e.g. Dec 31, 2021 was a full session.
- Early closes (13:00 ET): July 3 when it is itself a trading day, the day
  after Thanksgiving, and Christmas Eve when it is itself a trading day.
"""
from datetime import date, time as dtime
from functools import lru_cache

from pandas.tseries.holiday import (
    AbstractHolidayCalendar,
    GoodFriday,
    Holiday,
    USLaborDay,
    USMartinLutherKingJr,
    USMemorialDay,
    USPresidentsDay,
    USThanksgivingDay,
    nearest_workday,
    sunday_to_monday,
)

REGULAR_CLOSE = dtime(16, 0)
EARLY_CLOSE = dtime(13, 0)


class _NyseHolidayCalendar(AbstractHolidayCalendar):
    rules = [
        Holiday("New Year's Day", month=1, day=1, observance=sunday_to_monday),
        USMartinLutherKingJr,
        USPresidentsDay,
        GoodFriday,
        USMemorialDay,
        Holiday(
            "Juneteenth", month=6, day=19,
            observance=nearest_workday, start_date="2022-06-19",
        ),
        Holiday("Independence Day", month=7, day=4, observance=nearest_workday),
        USLaborDay,
        USThanksgivingDay,
        Holiday("Christmas Day", month=12, day=25, observance=nearest_workday),
    ]


@lru_cache(maxsize=8)
def _holidays_for_year(year: int) -> dict[date, str]:
    series = _NyseHolidayCalendar().holidays(
        start=f"{year}-01-01", end=f"{year}-12-31", return_name=True
    )
    return {ts.date(): name for ts, name in series.items()}


def holiday_name(d: date) -> str | None:
    """Holiday name if the exchange is closed all day on `d`, else None."""
    return _holidays_for_year(d.year).get(d)


def is_trading_day(d: date) -> bool:
    return d.weekday() < 5 and holiday_name(d) is None


def is_early_close(d: date) -> bool:
    """True on 13:00 ET half-days: July 3 (when trading — July 4 is then always
    a weekday holiday), the Friday after Thanksgiving, and Christmas Eve (when
    trading — i.e. Dec 24 falls Mon-Thu)."""
    if not is_trading_day(d):
        return False
    if (d.month, d.day) in ((7, 3), (12, 24)):
        return True
    return d.month == 11 and d.weekday() == 4 and holiday_name(d.replace(day=d.day - 1)) == "Thanksgiving Day"


def close_time(d: date) -> dtime:
    return EARLY_CLOSE if is_early_close(d) else REGULAR_CLOSE
