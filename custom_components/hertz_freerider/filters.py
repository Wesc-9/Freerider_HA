"""Pure ride normalization and conservative filter logic.

This module intentionally requires no Home Assistant dependency, for easy tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import unicodedata


@dataclass(frozen=True)
class Ride:
    """One offer reported by a source, with no inferred fields."""

    source_country: str
    source_id: str
    origin: str
    destination: str
    vehicle: str
    booking_url: str
    available_start: str | None = None
    available_end: str | None = None
    transmission: str | None = None  # automatic/manual, only when explicit
    vehicle_type: str | None = None  # car/van/minibus, only when explicit
    fuel: str | None = None  # electric/hybrid/petrol/diesel, only when explicit
    seats: int | None = None

    @property
    def key(self) -> str:
        """Stable listing identity for deduplication."""
        return f"{self.source_country}:{self.source_id}"

    def as_event(self) -> dict:
        """JSON-safe details for Home Assistant events and attributes."""
        return {
            "id": self.key,
            "country": self.source_country,
            "origin": self.origin,
            "destination": self.destination,
            "vehicle": self.vehicle,
            "booking_url": self.booking_url,
            "date_start": self.available_start,
            "date_end": self.available_end,
            "transmission": self.transmission,
            "vehicle_type": self.vehicle_type,
            "fuel": self.fuel,
            "seats": self.seats,
        }


def normalized(value: str | None) -> str:
    """Match Scandinavian names including ø/æ/å and basic diacritics."""
    value = (value or "").translate(str.maketrans({
        "ø": "o", "Ø": "O", "æ": "ae", "Æ": "AE", "å": "a", "Å": "A",
    }))
    return "".join(
        c for c in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(c)
    ).casefold().strip()


def ride_matches(ride: Ride, config: dict) -> bool:
    """Evaluate location, date, transmission and optional vehicle filters.

    When the user filters by metadata the provider did not disclose, the
    listing is NOT treated as a match. Exact/range dates overlap a provider's
    known offer availability window rather than assuming trip dates.
    """
    countries = config.get("countries", ["NO"])
    if ride.source_country not in countries:
        return False

    wanted_from = normalized(config.get("origin", ""))
    wanted_to = normalized(config.get("destination", ""))
    origin = normalized(ride.origin)
    destination = normalized(ride.destination)
    forward = wanted_from in origin and wanted_to in destination
    reverse = wanted_from in destination and wanted_to in origin
    if not (forward or (config.get("direction") == "either" and reverse)):
        return False

    date_mode = config.get("date_mode", "any")
    if date_mode != "any":
        if not ride.available_start or not ride.available_end:
            return False
        try:
            available_from = date.fromisoformat(ride.available_start)
            available_to = date.fromisoformat(ride.available_end)
            wanted_start = date.fromisoformat(config["date_start"])
            wanted_end = (
                date.fromisoformat(config["date_end"])
                if date_mode == "range" else wanted_start
            )
        except (TypeError, ValueError, KeyError):
            return False
        if wanted_end < available_from or wanted_start > available_to:
            return False

    for key, attr in (
        ("transmission", "transmission"),
        ("vehicle_type", "vehicle_type"),
        ("fuel", "fuel"),
    ):
        wanted = config.get(key, "any")
        if wanted != "any" and wanted != getattr(ride, attr):
            return False

    minimum_seats = int(config.get("min_seats", 0) or 0)
    if minimum_seats and (ride.seats is None or ride.seats < minimum_seats):
        return False
    return True


def filter_rides(rides: list[Ride], config: dict) -> list[Ride]:
    """Filter and sort results by the first known available date."""
    return sorted(
        (ride for ride in rides if ride_matches(ride, config)),
        key=lambda r: (r.available_start or "9999-12-31", r.origin.casefold(), r.key),
    )
