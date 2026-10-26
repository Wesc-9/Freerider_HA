"""Persist stations discovered from public Freerider route feeds.

The catalog belongs to this Home Assistant installation, not to Hertz or a
shared cloud service. It survives restarts, remembers stations after offers
expire and grows when route feeds expose new locations.
"""

from __future__ import annotations

import asyncio
import logging

from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .filters import Ride, merge_station_history, known_station_names

_LOGGER = logging.getLogger(__name__)
_KEY = f"{DOMAIN}_station_catalog"
_DATA_VERSION = 1


class StationCatalog:
    """Home Assistant-wide station history shared by every search profile."""

    def __init__(self, hass) -> None:
        self._store = Store(hass, _DATA_VERSION, _KEY)
        self._lock = asyncio.Lock()
        self._loaded = False
        self._countries: dict[str, list[str]] = {}

    async def async_load(self) -> None:
        """Read history once, protecting concurrent setup and polling."""
        if self._loaded:
            return
        async with self._lock:
            if self._loaded:
                return
            loaded = await self._store.async_load()
            if isinstance(loaded, dict):
                raw = loaded.get("countries", {})
                if isinstance(raw, dict):
                    self._countries = {
                        country: [x for x in values if isinstance(x, str)]
                        for country, values in raw.items()
                        if isinstance(country, str) and isinstance(values, list)
                    }
            self._loaded = True

    async def async_learn(self, country: str, rides: list[Ride]) -> int:
        """Keep all previously known stations and add newly seen ones.

        Only read-only provider offers count as new stations; arbitrary user
        search text is not published into the shared suggestion index.
        """
        await self.async_load()
        async with self._lock:
            countries, added = merge_station_history(self._countries, country, rides)
            if added:
                await self._store.async_save({"countries": countries})
                self._countries = countries
                _LOGGER.debug("Learned %s new Freerider stations for %s", added, country)
            return added

    def suggestions(self, countries: list[str]) -> list[str]:
        """Combine remembered station names for the selected source countries."""
        return known_station_names(self._countries, countries)


async def async_get_station_catalog(hass) -> StationCatalog:
    """Get or initialize the singleton shared by flows and coordinators."""
    key = f"{DOMAIN}_catalog_instance"
    catalog = hass.data.get(key)
    if catalog is None:
        catalog = StationCatalog(hass)
        # Assign before awaiting, so concurrent flows use the same lock.
        hass.data[key] = catalog
    await catalog.async_load()
    return catalog
