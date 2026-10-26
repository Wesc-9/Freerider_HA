"""Public Freerider route feeds used by the official Norwegian and Swedish sites.

The endpoint paths and country tokens were verified from the site's published
JavaScript and with live unauthenticated HTTP 200 JSON responses on 2026-10-26.
Hertz is not affiliated with this independent integration. Keep polling modest.
"""

from __future__ import annotations

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .filters import Ride, parse_transport_routes

ROUTE_API = {
    "NO": (
        "https://hertzfreerider.no/api/transport-routes/?country=NORWAY",
        "https://hertzfreerider.no/no-no/",
    ),
    "SE": (
        "https://hertzfreerider.se/api/transport-routes/?country=SWEDEN",
        "https://hertzfreerider.se/sv-se/",
    ),
}


class SourceNotReady(Exception):
    """Requested service has no verified public route source."""


async def async_fetch_country(hass, country: str) -> list[Ride]:
    """Download current routes; propagate errors instead of reporting zero."""
    if country not in ROUTE_API:
        if country == "DK":
            raise SourceNotReady(
                "Danish catalog requires JS, and stock can differ from "
                "catalog visibility. No validated permitted listing feed yet."
            )
        raise SourceNotReady(f"Unsupported Freerider country: {country}")

    url, booking_url = ROUTE_API[country]
    session = async_get_clientsession(hass)
    try:
        async with session.get(
            url,
            headers={"Accept": "application/json"},
            timeout=aiohttp.ClientTimeout(total=20),
        ) as response:
            response.raise_for_status()
            payload = await response.json(content_type=None)
    except (aiohttp.ClientError, TimeoutError, ValueError) as exc:
        raise SourceNotReady(f"{country}: Freerider feed unavailable: {exc}") from exc

    try:
        return parse_transport_routes(payload, country, booking_url)
    except (ValueError, TypeError, KeyError) as exc:
        raise SourceNotReady(f"{country}: unexpected Freerider response: {exc}") from exc
