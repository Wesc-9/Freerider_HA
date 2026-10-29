"""Explicit user-requested toll estimates for Norwegian Freerider routes.

No background polling of this calculator. One request consumes a quota call:
https://bompengeappen.no/api-docs
"""

from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .filters import Ride
from .toll_parser import parse_toll_response

ROUTE_API = "https://bompengeappen.no/api/route"


class TollLookupError(Exception):
    """No safe toll estimate was possible."""


def _station_coordinates(lat, lon) -> str:
    """Accept published Hertz latitude and longitude in normal degrees."""
    try:
        la, lo = float(lat), float(lon)
    except (TypeError, ValueError) as exc:
        raise TollLookupError("Hertz did not provide station coordinates") from exc
    if not all(map(isfinite, (la, lo))) or not (-90 <= la <= 90 and -180 <= lo <= 180):
        raise TollLookupError("Invalid Hertz station coordinates")
    return f"{la:.7f},{lo:.7f}"


async def async_estimate_toll(
    hass, ride: Ride, start_time: str | None = None, *, api_key: str | None = None,
) -> dict:
    """Calculate Norwegian local tolls using an explicit, manual request.

    The first recommended calculated road route need not match exactly the
    vehicle return instructions from Hertz. Reject cross-border estimates.
    """
    if not isinstance(api_key, str) or not api_key.strip():
        raise TollLookupError(
            "Mangler API-nøkkel fra BompengeAppen. Opprett gratis nøkkel på "
            "https://bompengeappen.no/api-portal og legg den inn under "
            "Freerider HA → Konfigurer → Bom og reisekostnader."
        )
    if ride.vehicle_type in ("van", "minibus"):
        raise TollLookupError(
            "Varebil/minibuss: ukjent tillatt totalvekt og bomtakstgruppe. "
            "Kan ikke gi pålitelig personbilestimat uten registrert kjøretøyklasse."
        )
    if (ride.pickup_country or "").lower() != "no" or (ride.return_country or "").lower() != "no":
        raise TollLookupError("Norwegian toll estimator supports NO-to-NO journeys only")
    # Country from station metadata, not merely the site the offer appeared on.
    origin = _station_coordinates(ride.pickup_lat, ride.pickup_lon)
    destination = _station_coordinates(ride.return_lat, ride.return_lon)
    params = {"from": origin, "to": destination, "refine": "1"}
    if start_time:
        try:
            datetime.fromisoformat(start_time)
        except (ValueError, TypeError) as exc:
            raise TollLookupError("start_time must be an ISO 8601 datetime") from exc
        params["startTime"] = start_time

    session = async_get_clientsession(hass)
    try:
        async with session.get(
            ROUTE_API,
            params=params,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key.strip()}",
            },
            timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            if response.status in (401, 403):
                raise TollLookupError(
                    "BompengeAppen avviste API-nøkkelen eller abonnementet. "
                    "Kontroller nøkkelen i API-portalen."
                )
            if response.status == 429:
                raise TollLookupError(
                    "BompengeAppen har nådd døgnkvoten. Prøv igjen etter reset."
                )
            response.raise_for_status()
            data = await response.json(content_type=None)
    except (aiohttp.ClientError, TimeoutError, ValueError) as exc:
        raise TollLookupError(f"Could not calculate Norwegian tolls: {exc}") from exc
    try:
        result = parse_toll_response(data, electric=(ride.fuel == "electric"))
    except ValueError as exc:
        raise TollLookupError(str(exc)) from exc
    result["road_checked_at"] = datetime.now(timezone.utc).isoformat()
    result["ride_id"] = ride.key
    result["from"] = ride.origin
    result["to"] = ride.destination
    result["calculated_for"] = start_time or "now (provider's local Norwegian time)"
    result["fuel_charging_note"] = "Fuel/charging costs may apply."
    if ride.fuel is None:
        result["vehicle_warning"] = (
            "Fuel type unknown: estimate uses regular small-car rate, "
            "not a verified vehicle-specific rate."
        )
    if ride.vehicle_type in ("van", "minibus"):
        result["vehicle_warning"] = (
            "Vehicle weight/length unknown: this is a SMALL vehicle toll "
            "estimate only; heavier vehicles may cost more."
        )
    return result
