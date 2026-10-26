"""Optional Home Assistant push notifications for newly discovered matching cars.

The legacy mobile_app notification service supports the clickAction/url fields
used by iOS and Android. This integration deliberately uses services whose
names are already registered in Home Assistant, not arbitrary external APIs.

Freerider's public booking-flow page supports a hash containing route ID
and pickup time. Prefer this first-party link for actual car alerts, while
retaining a safe fallback for stale offers or the generic test notification.
A direct link does not bypass authentication or guarantee booking.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from .filters import Ride

_LOGGER = logging.getLogger(__name__)

TARGET_OFF = "off"
TARGET_PERSISTENT = "persistent"
SAFE_HOSTS = frozenset({
    "hertzfreerider.no", "www.hertzfreerider.no",
    "hertzfreerider.se", "www.hertzfreerider.se",
    "hertzfreerider.nu", "www.hertzfreerider.nu",
})
KNOWN_LANDING = {
    "NO": "https://hertzfreerider.no/no-no/",
    "SE": "https://hertzfreerider.se/sv-se/",
    "DK": "https://hertzfreerider.nu/",
}


def official_url(value: str | None, country: str) -> str:
    """Only pass official HTTPS Freerider URLs to Companion app click actions."""
    if isinstance(value, str):
        url = urlsplit(value)
        if url.scheme == "https" and url.hostname in SAFE_HOSTS:
            return value
    return KNOWN_LANDING.get(country, KNOWN_LANDING["NO"])


def _local_datetime(value: str | None) -> str | None:
    """Format a published source timestamp without pretending timezone is known."""
    from datetime import datetime

    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed.strftime("%d.%m kl. %H:%M")


def _drive_summary(ride: Ride, language: str) -> str:
    """Use Hertz's own drive time and distance, never crow-flies estimates."""
    norwegian = language.lower().startswith(("nb", "nn", "no"))
    distance = ride.distance_km
    minutes = ride.drive_minutes
    parts = []
    if distance is not None and distance > 0:
        parts.append(f"{distance:g} km")
    if minutes is not None and minutes > 0:
        rounded = int(round(minutes))
        hours, mins = divmod(rounded, 60)
        duration = (f"{hours} t {mins} min" if hours else f"{mins} min") if norwegian else (
            f"{hours}h {mins}m" if hours else f"{mins}m"
        )
        parts.append(("ca. " if norwegian else "approx. ") + duration)
    return " · ".join(parts) if parts else (
        "Kjøretid og distanse ikke oppgitt" if norwegian else
        "Driving time and distance not provided"
    )


def _toll_summary(quote: dict | None, reason: str, language: str) -> str:
    """Show cost only when backed by a successful Norwegian estimate."""
    norwegian = language.lower().startswith(("nb", "nn", "no"))
    if quote is not None and quote.get("amount_nok") is not None:
        amount = float(quote["amount_nok"])
        formatted = f"{amount:,.0f}".replace(",", " ")
        result = (
            f"Bom ca. {formatted} kr (anslag, uten AutoPASS-rabatt)"
            if norwegian else
            f"Tolls approx. NOK {formatted} (estimate, no AutoPASS discount)"
        )
        if quote.get("ferry_count"):
            result += (
                " · Ferge ikke inkludert" if norwegian
                else " · Ferries not included"
            )
        if quote.get("vehicle_warning"):
            result += (
                " · Biltakst usikker" if norwegian
                else " · Vehicle tariff uncertain"
            )
        return result

    if reason == "outside_norway":
        return (
            "Bom: Ikke beregnet utenfor Norge"
            if norwegian else "Tolls: Not calculated outside Norway"
        )
    if reason == "unknown_heavy_vehicle_rate":
        return (
            "Bom: Ukjent takst for større kjøretøy"
            if norwegian else "Tolls: Heavy-vehicle rate unknown"
        )
    if reason in ("daily_limit", "scan_limit"):
        return (
            "Bom: Ikke beregnet (daglig grense)"
            if norwegian else "Tolls: Not calculated (usage cap)"
        )
    return (
        "Bom: Estimat ikke tilgjengelig" if norwegian
        else "Tolls: Estimate unavailable"
    )


def notification_content(
    ride: Ride,
    name: str,
    language: str = "nb",
    toll_estimate: dict | None = None,
    toll_status: str = "not_calculated",
    now=None,
) -> dict:
    """Detailed and readable push with real vehicle/route/travel data."""
    if __package__:
        from .booking_links import official_car_booking_url
    else:
        from booking_links import official_car_booking_url

    url, direct = official_car_booking_url(ride, now=now)
    norwegian = language.lower().startswith(("nb", "nn", "no"))
    available = _local_datetime(ride.available_at)
    latest_return = _local_datetime(ride.latest_return_at)
    expiry = _local_datetime(ride.offer_expires_at)
    if norwegian:
        title = "🚗 Ny Freerider-bil!"
        lines = [
            f"📍 {ride.origin} → {ride.destination}",
            f"🚙 {ride.vehicle}",
            f"🛣️ {_drive_summary(ride, language)}",
        ]
        if available:
            lines.append(f"📅 Tilgjengelig fra {available}")
        if expiry:
            lines.append(f"⏳ Tilbudet utløper {expiry}")
        if latest_return:
            lines.append(f"🏁 Siste retur {latest_return}")
        lines.extend([
            f"💳 {_toll_summary(toll_estimate, toll_status, language)}",
            "⛽ Drivstoff/lading kan forekomme",
            (f"Tilbud {ride.key} · Trykk for å åpne denne bilen"
             if direct else f"Tilbud {ride.key} · Åpne Freerider og finn bilen"),
        ])
    else:
        title = "🚗 New Freerider car!"
        lines = [
            f"📍 {ride.origin} → {ride.destination}",
            f"🚙 {ride.vehicle}",
            f"🛣️ {_drive_summary(ride, language)}",
        ]
        if available:
            lines.append(f"📅 Available from {available}")
        if expiry:
            lines.append(f"⏳ Offer expires {expiry}")
        if latest_return:
            lines.append(f"🏁 Return by {latest_return}")
        lines.extend([
            f"💳 {_toll_summary(toll_estimate, toll_status, language)}",
            "⛽ Fuel/charging costs may apply",
            (f"Offer {ride.key} · Tap to open this car"
             if direct else f"Offer {ride.key} · Open Freerider to find this car"),
        ])
    return {
        "title": title,
        "message": "\n".join(lines),
        "url": url,
        "route": f"{ride.origin} → {ride.destination}",
        "direct_car_link": direct,
    }


def test_notification_content(name: str, language: str = "nb") -> dict:
    """A clear test, not a fabricated car offer."""
    norwegian = language.lower().startswith(("nb", "nn", "no"))
    return {
        "title": "Freerider HA · Testvarsel" if norwegian else "Freerider HA · Test notification",
        "message": (
            f"Testvarsel for «{name}». Dette er ikke en konkret bil. Ekte treff åpner bestillingsflyten for den aktuelle bilen."
            if norwegian else
            f"Test for “{name}”. No car is attached to this test. Real car alerts link to that specific car's booking flow."
        ),
        "url": KNOWN_LANDING["NO"],
    }


def notification_targets(hass, configured: str | None = None) -> list[tuple[str, str]]:
    """Read active mobile app notification services, never guess phone names."""
    all_services = hass.services.async_services().get("notify", {})
    options = [(TARGET_OFF, "Off / disabled"), (TARGET_PERSISTENT, "Home Assistant notifications")]
    for service in sorted(all_services):
        if service.startswith("mobile_app_"):
            options.append((f"mobile_app:{service}", f"Mobile app · {service.removeprefix('mobile_app_').replace('_', ' ')}"))
    # Preserve configuration even if the user's phone is currently disconnected
    if configured and configured not in [value for value, _ in options]:
        options.append((configured, f"Previously selected · {configured}"))
    return options


async def async_send_notification(hass, target: str, payload: dict) -> bool:
    """Send to configured destination; never send to a different random device."""
    if not target or target == TARGET_OFF:
        return False
    message = payload["message"]
    url = payload["url"]
    if target == TARGET_PERSISTENT:
        # Persistent notification supports Markdown. It stays in the HA UI.
        data = {
            "title": payload["title"],
            "message": f"{message}\n\n[Åpne Freerider]({url})",
        }
        await hass.services.async_call("persistent_notification", "create", data, blocking=True)
        return True
    if target.startswith("mobile_app:"):
        service = target.removeprefix("mobile_app:")
        # Validate against actual registered services before calling.
        if not service.startswith("mobile_app_") or not hass.services.has_service("notify", service):
            _LOGGER.warning("Freerider HA mobile notification target is unavailable: %s", target)
            return False
        await hass.services.async_call(
            "notify",
            service,
            {
                "title": payload["title"],
                "message": message,
                "data": {"url": url, "clickAction": url},
            },
            blocking=True,
        )
        return True
    _LOGGER.warning("Unrecognized Freerider HA notification target: %s", target)
    return False
