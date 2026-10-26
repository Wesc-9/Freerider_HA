"""Country-specific official data adapters.

DO NOT guess hidden endpoints, scrape protected pages or fabricate offers.
The public websites are known, but machine-readable authorized listing sources
have not yet been established for any country.
"""

from __future__ import annotations

from .const import COUNTRIES, OFFICIAL_SITES
from .filters import Ride


class SourceNotReady(Exception):
    """The data source has not been validated and implemented."""


async def async_fetch_country(country: str) -> list[Ride]:
    """Return real parsed offers from a future verified provider adapter."""
    if country not in COUNTRIES:
        raise SourceNotReady(f"Unsupported Freerider country: {country}")
    raise SourceNotReady(
        f"No verified listing data adapter for {COUNTRIES[country]} "
        f"({OFFICIAL_SITES[country]})"
    )
