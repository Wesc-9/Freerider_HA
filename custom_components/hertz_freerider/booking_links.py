"""Construct per-car Freerider booking links using the provider's own URL contract.

The official booking-flow JavaScript reads #id=<route.id>&date=<ISO local time>
and looks up that offer before continuing to authentication/checkout. This
module never automates booking or bypasses user sign-in. Invalid/expired
offers fall back to the public list, not to a made-up reservation URL.
"""

from __future__ import annotations

from datetime import datetime, timedelta, time
from typing import TYPE_CHECKING
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from .filters import Ride

BOOKING_FLOW = {
    "NO": "https://hertzfreerider.no/booking-flow/no-no/",
    "SE": "https://hertzfreerider.se/booking-flow/sv-se/",
}
LANDING = {
    "NO": "https://hertzfreerider.no/no-no/",
    "SE": "https://hertzfreerider.se/sv-se/",
}
ZONE = ZoneInfo("Europe/Oslo")
MAX_LOOKAHEAD_DAYS = 21


def _date(text: str | None) -> datetime | None:
    """Interpret provider local time (NO and SE use the same CET/CEST clock)."""
    if not text or not isinstance(text, str):
        return None
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is not None:
            return dt.astimezone(ZONE).replace(tzinfo=None)
        return dt
    except ValueError:
        return None


def _opening_time(value: object) -> time | None:
    """The feed represents time as a placeholder-date ISO datetime."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value).time()
    except ValueError:
        return None


def _ceil_quarter(dt: datetime) -> datetime:
    """Prefer exact quarter-hour selections in the booking calendar."""
    dt = dt.replace(second=0, microsecond=0)
    rem = dt.minute % 15
    return dt + timedelta(minutes=(15 - rem) % 15)


def _candidate_time(ride: Ride, now: datetime) -> datetime | None:
    """Find a feasible future pickup within the published offer window.

    A selected pickup date is needed for the official site's deep-link
    validation. Prefer staffed opening hours when provided. The site's own
    validator is authoritative for exceptional holiday and kiosk rules.
    """
    available = _date(ride.available_at)
    expire = _date(ride.offer_expires_at)
    latest_return = _date(ride.latest_return_at)
    if available is None or expire is None or latest_return is None:
        return None
    if ride.drive_minutes is None or ride.drive_minutes <= 0:
        return None
    start = _ceil_quarter(max(available, now + timedelta(minutes=45)))
    deadline = min(expire, latest_return - timedelta(minutes=ride.drive_minutes))
    if start > deadline:
        return None

    schedule = getattr(ride, "pickup_opening_hours", None)
    if not isinstance(schedule, dict) or not schedule:
        # The source has no published opening hours; the official booking
        # flow will perform its own remaining eligibility checks.
        return start

    for day_offset in range(min(MAX_LOOKAHEAD_DAYS, (deadline.date() - start.date()).days + 1)):
        day = start.date() + timedelta(days=day_offset)
        slot = schedule.get(str(day.isoweekday()))
        if not isinstance(slot, dict):
            continue
        opens = _opening_time(slot.get("openingTime"))
        closes = _opening_time(slot.get("closingTime"))
        if opens is None or closes is None or closes <= opens:
            continue
        # Don't send customers exactly at closing time.
        beginning = datetime.combine(day, opens) + timedelta(minutes=15)
        end = datetime.combine(day, closes) - timedelta(minutes=15)
        attempt = _ceil_quarter(max(start, beginning))
        if attempt <= end and attempt <= deadline:
            return attempt
    return None


def official_car_booking_url(
    ride: Ride, now: datetime | None = None
) -> tuple[str, bool]:
    """Get official deep link and whether it targets a specific car.

    Returns a safe country-level fallback for stale or incomplete offers.
    A deep link opens the provider's booking process, not a confirmed booking.
    """
    country = ride.source_country
    fallback = LANDING.get(country, LANDING["NO"])
    prefix = BOOKING_FLOW.get(country)
    if prefix is None or not str(ride.source_id).isdigit():
        return fallback, False

    now_value = now or datetime.now(ZONE)
    if now_value.tzinfo is not None:
        now_value = now_value.astimezone(ZONE).replace(tzinfo=None)
    candidate = _candidate_time(ride, now_value)
    if candidate is None:
        return fallback, False

    # First-party contract from booking-flow JS: URLSearchParams(location.hash)
    # expects literal id and date fields; the 'insurances' field is optional.
    fragment = urlencode({
        "id": str(ride.source_id),
        "date": candidate.strftime("%Y-%m-%dT%H:%M"),
    })
    return prefix + "#" + fragment, True
