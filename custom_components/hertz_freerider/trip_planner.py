"""Pure trip screening, ranking and notification quiet-time helpers.

Published Freerider timestamps usually have no timezone. Treat them as local
wall times for comparisons, not as a guarantee of station opening/booking.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .filters import Ride

PICKUP_BUFFER_MINUTES = 30


def _date(value: str | None) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value)
        return dt.replace(tzinfo=None)
    except ValueError:
        return None


def journey_feasibility(ride: Ride, now: datetime | None = None) -> dict:
    """Estimate spare time after pickup buffer and driving.

    Not a verified rental availability result; pickup desk opening hours,
    rest stops and traffic cannot be checked here.
    """
    if now is None:
        now = datetime.now()
    now = now.replace(tzinfo=None)
    first = _date(ride.available_at)
    expires = _date(ride.offer_expires_at)
    returned = _date(ride.latest_return_at)
    minutes = ride.drive_minutes
    if not returned or not isinstance(minutes, (int,float)) or not 0 < minutes < 100000:
        return {"status": "unknown", "margin_minutes": None,
                "reason": "no_verified_return_or_drive_time"}
    if expires and now > expires:
        return {"status": "expired", "margin_minutes": None,
                "reason": "listing_expired"}
    proposed_pickup = max(now, first) if first else now
    latest_arrival = proposed_pickup + timedelta(minutes=float(minutes) + PICKUP_BUFFER_MINUTES)
    margin = round((returned - latest_arrival).total_seconds() / 60)
    if margin < 0:
        status = "insufficient"
    elif margin < 120:
        status = "tight"
    else:
        status = "comfortable"
    return {
        "status": status,
        "margin_minutes": margin,
        "assumed_pickup_at": proposed_pickup.isoformat(timespec="minutes"),
        "pickup_buffer_minutes": PICKUP_BUFFER_MINUTES,
        "reason": "estimate_only_not_booking_confirmation",
    }


def km_airline(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance, explicitly not driving distance."""
    a1, b1, a2, b2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat, dlon = a2-a1, b2-b1
    hav = sin(dlat/2)**2 + cos(a1)*cos(a2)*sin(dlon/2)**2
    return 6371.009 * 2 * asin(min(1.0, sqrt(hav)))


SORT_MODES = {
    "date", "short_drive", "short_route", "nearest_pickup", "low_cost", "best_margin",
}


def sort_offers(rides: list[Ride], mode: str, costs: dict[str, dict] | None = None,
                home: tuple[float,float] | None = None, now: datetime | None = None) -> list[Ride]:
    """Rank with missing information LAST, never pretend missing cost equals 0."""
    costs = costs or {}
    if mode not in SORT_MODES or mode == "date":
        return list(rides)

    def metric(ride: Ride) -> float | None:
        if mode == "short_drive":
            return ride.drive_minutes
        if mode == "short_route":
            return ride.distance_km
        if mode == "nearest_pickup":
            if not home or ride.pickup_lat is None or ride.pickup_lon is None:
                return None
            return km_airline(home[0], home[1], ride.pickup_lat, ride.pickup_lon)
        if mode == "low_cost":
            value = costs.get(ride.key, {}).get("known_subtotal_nok")
            return value if isinstance(value, (int,float)) else None
        if mode == "best_margin":
            margin = journey_feasibility(ride, now).get("margin_minutes")
            return -float(margin) if margin is not None else None
        return None

    return sorted(
        rides,
        key=lambda ride: (
            metric(ride) is None,
            metric(ride) if metric(ride) is not None else float("inf"),
            ride.available_start or "9999-12-31",
            ride.key,
        ),
    )


def quiet_now(start: str | None, end: str | None, now: datetime) -> bool:
    """Support windows crossing midnight; blank or equal times means off."""
    if not start or not end or start == end:
        return False
    try:
        begin = datetime.strptime(start,"%H:%M").time()
        finish = datetime.strptime(end,"%H:%M").time()
    except ValueError:
        return False
    clock = now.time()
    return begin <= clock < finish if begin < finish else (clock >= begin or clock < finish)


def is_urgent(ride: Ride, now: datetime, threshold_minutes: int = 180) -> bool:
    """Urgency from a published expiry, not a guessed pickup time."""
    expires = _date(ride.offer_expires_at)
    if not expires:
        return False
    left = (expires - now.replace(tzinfo=None)).total_seconds() / 60
    return 0 <= left <= threshold_minutes
