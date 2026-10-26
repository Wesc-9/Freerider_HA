"""Pure display helpers for individual available Freerider offers.

The full vehicle description is never guessed or rewritten.
The Home Assistant device overview shows a bounded number of current
offers, while the original count sensor still tracks every matching ride.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .filters import Ride

DEVICE_OFFER_LIMIT = 8


def device_offers(rides: list[Ride] | None, limit: int = DEVICE_OFFER_LIMIT) -> list[Ride]:
    """Stable first offers, deduplicated by source listing identity."""
    seen: set[str] = set()
    result: list[Ride] = []
    for ride in rides or ():
        if ride.key in seen:
            continue
        seen.add(ride.key)
        result.append(ride)
        if len(result) == limit:
            break
    return result


def offer_entity_name(ride: Ride) -> str:
    """Preserve exactly the provider's vehicle string and add the destination."""
    return f"{ride.vehicle} · {ride.destination}"


def offer_entity_state(ride: Ride) -> str:
    """Concise source-to-destination label for Home Assistant sensor rows."""
    return f"{ride.origin} → {ride.destination}"[:255]
