"""Optional Home Assistant push notifications for newly discovered matching cars.

The legacy mobile_app notification service supports the clickAction/url fields
used by iOS and Android. This integration deliberately uses services whose
names are already registered in Home Assistant, not arbitrary external APIs.

The Freerider site currently uses a browser session for selecting routes. The
public transport routes API does not guarantee a direct single-offer URL.
Only link to known official Freerider domains and include enough text to find
the matching offer; never fabricate a deep link.
"""

from __future__ import annotations

import logging
from urllib.parse import urlsplit

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


def notification_content(ride: Ride, name: str) -> dict:
    """Build an accurate user-facing message with route details and URL."""
    url = official_url(ride.booking_url, ride.source_country)
    when = f" · Fra {ride.available_start}" if ride.available_start else ""
    title = f"Freerider HA · Ny bil ({name})"
    body = (
        f"{ride.origin} → {ride.destination}\n"
        f"{ride.vehicle}{when}\n"
        f"Tilbuds-ID: {ride.key}\n"
        "Åpne Freerider for å finne og bestille bilen. "
        "Bompenger og drivstoff/lading kan forekomme."
    )
    return {"title": title, "message": body, "url": url}


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
