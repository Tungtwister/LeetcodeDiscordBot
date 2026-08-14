"""Shared configuration, so the reminder schedule and the check-in calendar agree.

Everything that decides "what day is it" must go through here. The obvious
`date.today()` returns the *host's* local date, which is UTC inside a container.
That boundary lands mid-evening in US timezones, so an evening check-in would be
filed under the next day: streaks break on days you actually practiced, and the
reminder pings people who already checked in.
"""

import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "UTC")
TZ = ZoneInfo(APP_TIMEZONE)


def today() -> date:
    """Today's date in APP_TIMEZONE, not the host's timezone."""
    return datetime.now(TZ).date()


def now_iso() -> str:
    """Current timezone-aware timestamp, for audit columns."""
    return datetime.now(TZ).isoformat()
