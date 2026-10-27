"""Pure ride normalization and conservative filter logic.

This module intentionally requires no Home Assistant dependency, for easy tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import unicodedata
import re

if __package__:
    from .search_enhancements import matches_model, station_in_radius
else:
    from search_enhancements import matches_model, station_in_radius


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
    distance_km: float | None = None
    drive_minutes: float | None = None
    available_at: str | None = None
    offer_expires_at: str | None = None
    latest_return_at: str | None = None
    pickup_lat: float | None = None
    pickup_lon: float | None = None
    return_lat: float | None = None
    return_lon: float | None = None
    pickup_country: str | None = None
    pickup_opening_hours: dict | None = None
    return_country: str | None = None

    @property
    def key(self) -> str:
        """Stable listing identity for deduplication."""
        return f"{self.source_country}:{self.source_id}"

    def as_event(self) -> dict:
        """JSON-safe listing details with a car-specific booking link."""
        if __package__:
            from .booking_links import official_car_booking_url
        else:
            from booking_links import official_car_booking_url

        booking_url, deep_link = official_car_booking_url(self)
        return {
            "id": self.key,
            "country": self.source_country,
            "origin": self.origin,
            "destination": self.destination,
            "vehicle": self.vehicle,
            "booking_url": booking_url,
            "official_site_url": self.booking_url,
            "direct_booking_link": deep_link,
            "date_start": self.available_start,
            "date_end": self.available_end,
            "transmission": self.transmission,
            "vehicle_type": self.vehicle_type,
            "fuel": self.fuel,
            "seats": self.seats,
            "distance_km": self.distance_km,
            "drive_minutes": self.drive_minutes,
            "pickup_lat": self.pickup_lat,
            "pickup_lon": self.pickup_lon,
            "return_lat": self.return_lat,
            "return_lon": self.return_lon,
            "available_at": self.available_at,
            "offer_expires_at": self.offer_expires_at,
            "latest_return_at": self.latest_return_at,
            "toll_note": "Tolls may be charged. Fuel/charging costs may apply.",
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


def place_values(value: object) -> list[str]:
    """Normalize multi-select values, keeping old single-string entries.

    Do not split on commas, which can occur inside station names.
    """
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, (list, tuple)):
        items = [item for item in value if isinstance(item, str)]
    else:
        items = []
    places: dict[str, str] = {}
    for item in items:
        item = item.strip()
        if item:
            places.setdefault(normalized(item), item)
    return list(places.values())


def station_matches(option: str, station: str) -> bool:
    """Match names conservatively, including known public airport aliases.

    'Værnes' is a common name for Trondheim Airport, which can be published
    as 'TRONDHEIM LUFTHAVN' in Freerider's listing feed.
    """
    needle = normalized(option)
    location = normalized(station)
    if needle in location:
        return True
    if needle in {"vaernes", "vaernes lufthavn", "trondheim vaernes"}:
        return "trondheim lufthavn" in location or "trondheim airport" in location
    return False


def ride_matches(ride: Ride, config: dict) -> bool:
    """Evaluate location, date, transmission and optional vehicle filters.

    When the user filters by metadata the provider did not disclose, the
    listing is NOT treated as a match. Exact/range dates overlap a provider's
    known offer availability window rather than assuming trip dates.
    """
    countries = config.get("countries", ["NO"])
    if ride.source_country not in countries:
        return False

    # OR across alternatives in a column, AND between From and To columns.
    # Existing single-string searches are still supported after upgrading.
    wanted_from = place_values(config.get("origin"))
    wanted_to = place_values(config.get("destination"))
    def _place_ok(names, place, lat, lon, side):
        # New sliders independently expand all GPS-confirmed selected points;
        # old profiles continue using the legacy one-center radius settings.
        new_key = f"{side}_radius_km"
        if new_key in config:
            radius = int(config.get(new_key, 0) or 0)
            points = config.get(f"{side}_radius_points") or []
        else:
            radius = int(config.get("radius_km", 0) or 0)
            old = config.get(f"{side}_radius_point")
            points = [old] if config.get(f"{side}_radius_name") and old else []
        has_radius = radius > 0 and bool(points)
        if not names and not has_radius:
            return True
        return (
            any(station_matches(x, place) for x in names)
            or (has_radius and any(
                station_in_radius(point, lat, lon, radius) for point in points
            ))
        )

    forward = (
        _place_ok(wanted_from,ride.origin,ride.pickup_lat,ride.pickup_lon,"origin")
        and _place_ok(wanted_to,ride.destination,ride.return_lat,ride.return_lon,"destination")
    )
    reverse = (
        _place_ok(wanted_from,ride.destination,ride.return_lat,ride.return_lon,"origin")
        and _place_ok(wanted_to,ride.origin,ride.pickup_lat,ride.pickup_lon,"destination")
    )
    if not (forward or (config.get("direction") == "either" and reverse)):
        return False
    if not matches_model(ride.vehicle, config.get("model_include"), config.get("model_exclude")):
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


def _explicit_transmission(model: str) -> str | None:
    """Recognize explicitly labeled gearboxes; never guess from the model."""
    if re.search(r"\bMAN(?:UAL|UELL)?\b", model, re.I):
        return "manual"
    if re.search(r"\bAUT(?:OMAT(?:IC)?)?\b", model, re.I):
        return "automatic"
    return None


def _explicit_fuel(model: str) -> str | None:
    """Only classify fuel from recognizable words in the public model string."""
    if re.search(r"\b(PHEV|HEV|HYBRID|LADDHYBRID)\b", model, re.I):
        return "hybrid"
    if re.search(r"\b(ELECTRIC|ELECTRI|ELBIL|ELBILEN|EL)\b", model, re.I):
        return "electric"
    if re.search(r"\b(DIESEL|TDCI)\b", model, re.I):
        return "diesel"
    if re.search(r"\b(BENSIN|BENS|PETROL)\b", model, re.I):
        return "petrol"
    return None


def _explicit_vehicle_type(model: str) -> str | None:
    """Conservative class hints from named commercial vehicle models.

    Vehicle category is NOT a verified Norwegian toll weight class. In
    particular, a Crafter can have different permitted gross weights; it must
    not automatically receive a <= 3,500 kg toll estimate.
    """
    if re.search(r"\b(MINIBUSS|MINIBUS|MINI[ -]?BUS|\d{2}[ -]?SETER)\b", model, re.I):
        return "minibus"
    if re.search(
        r"\b(CRAFTER|SPRINTER|DUCATO|BOXER|JUMPER|MASTER|MOVANO|"
        r"VITO|VIVARO|TRAFIC|PROACE|TRANSIT|TRANSPORTER|"
        r"CADDY|KANGOO|BERLINGO|PARTNER|VAREBIL|VAN|"
        r"PANEL[ -]?VAN|KASSEVOGN)\b|\b\d{1,2}[ ]?M(?:3|³)\b",
        model, re.I,
    ):
        return "van"
    if re.search(r"\b(SUV|PERSONBIL)\b", model, re.I):
        return "car"
    return None


def _explicit_seats(model: str) -> int | None:
    match = re.search(r"\b(\d{1,2})[ -]?(?:SETER|SITS|SITTPLASSER|SEATER)\b", model, re.I)
    return int(match.group(1)) if match else None


def _positive_number(value: object) -> float | None:
    """Accept valid positive numeric provider metrics, reject unknown/invalid."""
    from math import isfinite
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        return None
    value = float(value)
    return round(value, 1) if isfinite(value) and value > 0 else None


def parse_transport_routes(payload: object, country: str, booking_url: str) -> list[Ride]:
    """Normalize the publicly returned Hertz route groups.

    The API's 'availableAt' is the earliest published availability.
    'expireTime' is the listing expiry (NOT a guaranteed last pickup time).
    Filter dates conservatively against that advertised time span.
    'latestReturn' is a return deadline, never treated as a pickup time.
    """
    if not isinstance(payload, list):
        raise ValueError("Expected a list of Hertz Freerider route groups")
    rides: dict[str, Ride] = {}
    for group in payload:
        if not isinstance(group, dict) or not isinstance(group.get("routes"), list):
            continue
        for item in group["routes"]:
            if not isinstance(item, dict):
                continue
            offer_id = item.get("id")
            if offer_id is None:
                continue
            pickup = item.get("pickupLocation") or {}
            dropoff = item.get("returnLocation") or {}
            if not isinstance(pickup, dict) or not isinstance(dropoff, dict):
                continue
            origin = str(pickup.get("name") or group.get("pickupLocationName") or "").strip()
            destination = str(dropoff.get("name") or group.get("returnLocationName") or "").strip()
            if not origin or not destination:
                continue
            model = str(item.get("carModel") or "").strip()
            available_at = item.get("availableAt")
            expires_at = item.get("expireTime")
            latest_return = item.get("latestReturn")
            # Only accept actual public ISO datetime strings.
            available_at = available_at if isinstance(available_at, str) and len(available_at) >= 10 else None
            expires_at = expires_at if isinstance(expires_at, str) and len(expires_at) >= 10 else None
            latest_return = latest_return if isinstance(latest_return, str) and len(latest_return) >= 10 else None
            ride = Ride(
                source_country=country,
                source_id=str(offer_id),
                origin=origin,
                destination=destination,
                vehicle=model or "Unspecified vehicle",
                booking_url=booking_url,
                available_start=available_at[:10] if available_at else None,
                available_end=expires_at[:10] if expires_at else None,
                transmission=_explicit_transmission(model),
                vehicle_type=_explicit_vehicle_type(model),
                fuel=_explicit_fuel(model),
                seats=_explicit_seats(model),
                distance_km=_positive_number(item.get("distance")),
                drive_minutes=_positive_number(item.get("travelTime")),
                available_at=available_at,
                offer_expires_at=expires_at,
                latest_return_at=latest_return,
                pickup_lat=pickup.get("geoLat"),
                pickup_lon=pickup.get("geoLon"),
                return_lat=dropoff.get("geoLat"),
                return_lon=dropoff.get("geoLon"),
                pickup_country=pickup.get("country"),
                pickup_opening_hours=(
                    pickup.get("regularOpeningHours")
                    if isinstance(pickup.get("regularOpeningHours"), dict) else None
                ),
                return_country=dropoff.get("country"),
            )
            rides[ride.key] = ride
    return list(rides.values())


def station_candidates(rides: list[Ride]) -> list[str]:
    """Unique, accent-safe station suggestions from live route destinations.

    Suggestions never limit custom free-text searches. Include endpoints in
    both directions to allow searching all stations and cross-border returns.
    """
    names: dict[str, str] = {}
    for ride in rides:
        for candidate in (ride.origin, ride.destination):
            name = candidate.strip()
            key = normalized(name)
            if name and key:
                names.setdefault(key, name)
    return sorted(names.values(), key=normalized)


def merge_station_history(
    history: dict[str, list[str]], country: str, rides: list[Ride]
) -> tuple[dict[str, list[str]], int]:
    """Add new station names without losing ones from expired offers.

    No cross-user network storage; data is kept locally in Home Assistant.
    Country key is the official Freerider source, not necessarily a geographic
    boundary (cross-border routes may legitimately appear in either feed).
    """
    if country not in ("NO", "SE", "DK"):
        return history, 0
    original = history.get(country, [])
    names: dict[str, str] = {}
    for item in original:
        if isinstance(item, str):
            item = item.strip()
            if item and len(item) <= 160:
                names.setdefault(normalized(item), item)
    before = len(names)
    for item in station_candidates(rides):
        if len(item) <= 160:
            names.setdefault(normalized(item), item)
    added = len(names) - before
    if not added:
        return history, 0
    merged = dict(history)
    merged[country] = sorted(names.values(), key=normalized)
    return merged, added


def known_station_names(
    history: dict[str, list[str]], countries: list[str]
) -> list[str]:
    """Unique station dropdown choices for requested sources, including old."""
    names: dict[str, str] = {}
    for country in countries:
        for item in history.get(country, []):
            if isinstance(item, str) and item.strip():
                item = item.strip()
                names.setdefault(normalized(item), item)
    return sorted(names.values(), key=normalized)
