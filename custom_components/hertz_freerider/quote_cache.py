"""Quota-aware, Home Assistant-wide cache of optional Norwegian toll estimates.

Only NEW matching car alerts trigger an automatic lookup. A small daily cap
protects public keyless API usage (which is shared by IP with other clients).
The saved cache is shared by every watch and survives Home Assistant restarts.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
from zoneinfo import ZoneInfo

from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .tolls import TollLookupError, async_estimate_toll

_LOGGER = logging.getLogger(__name__)
MAX_AUTO_DAILY = 10
CACHE_HOURS = 20
STORE_VERSION = 1
NORWAY_ZONE = ZoneInfo("Europe/Oslo")


def quote_eligibility(ride) -> str:
    """Return a reason why automatic toll lookup cannot be trusted."""
    if (ride.pickup_country or "").lower() != "no" or (ride.return_country or "").lower() != "no":
        return "outside_norway"
    if ride.vehicle_type in ("van", "minibus"):
        return "unknown_heavy_vehicle_rate"
    for coordinate in (ride.pickup_lat, ride.pickup_lon, ride.return_lat, ride.return_lon):
        if coordinate is None:
            return "missing_coordinates"
    return "ok"


class RouteQuoteCatalog:
    """Persist cached estimates and small daily quota across HA restarts."""

    def __init__(self, hass) -> None:
        self.hass = hass
        self._store = Store(hass, STORE_VERSION, f"{DOMAIN}_alert_route_quotes")
        self._lock = asyncio.Lock()
        self._loaded = False
        self._quotes: dict[str, dict] = {}
        self._day: str = ""
        self._count: int = 0

    async def _load_locked(self) -> None:
        if self._loaded:
            return
        data = await self._store.async_load()
        if isinstance(data, dict):
            quotes = data.get("quotes")
            if isinstance(quotes, dict):
                self._quotes = {
                    str(key): value for key, value in quotes.items()
                    if isinstance(value, dict)
                }
            if isinstance(data.get("day"), str):
                self._day = data["day"]
            self._count = max(0, int(data.get("count") or 0))
        self._loaded = True

    def _cache_key(self, ride) -> str:
        """Route and fuel category; never depend on mutable user-visible names."""
        return ":".join([
            *(f"{float(v):.5f}" for v in (
                ride.pickup_lat, ride.pickup_lon,
                ride.return_lat, ride.return_lon,
            )),
            "ev" if ride.fuel == "electric" else "combustion_or_unknown",
        ])

    async def async_quote(self, ride) -> tuple[dict | None, str]:
        """Best-effort estimate. Never block delivery due to rate limits.

        Shared lock prevents separate watch profiles from simultaneously
        exhausting today's daily budget or duplicating the same route.
        """
        why = quote_eligibility(ride)
        if why != "ok":
            return None, why

        async with self._lock:
            await self._load_locked()
            today = datetime.now(NORWAY_ZONE).date().isoformat()
            if today != self._day:
                self._day = today
                self._count = 0

            key = self._cache_key(ride)
            now = datetime.now(NORWAY_ZONE)
            cached = self._quotes.get(key)
            if cached:
                try:
                    age = now - datetime.fromisoformat(cached["timestamp"])
                    if timedelta(0) <= age < timedelta(hours=CACHE_HOURS):
                        return dict(cached["estimate"]), "cached"
                except (ValueError, TypeError, KeyError):
                    pass

            if self._count >= MAX_AUTO_DAILY:
                return None, "daily_limit"

            # Count BEFORE the call to avoid exceeding keyless shared quotas
            # after timeouts/network errors or if Home Assistant restarts.
            self._count += 1
            await self._save_locked()
            try:
                estimate = await async_estimate_toll(self.hass, ride)
            except (TollLookupError, Exception) as exc:
                _LOGGER.debug("Toll estimate unavailable for %s: %s", ride.key, exc)
                return None, "provider_error"

            self._quotes[key] = {
                "timestamp": now.isoformat(),
                "estimate": estimate,
            }
            # Keep storage bounded and preserve the newest successful quotes.
            if len(self._quotes) > 150:
                oldest = sorted(
                    self._quotes, key=lambda k: self._quotes[k].get("timestamp", "")
                )
                for k in oldest[:len(self._quotes) - 150]:
                    self._quotes.pop(k, None)
            await self._save_locked()
            return dict(estimate), "calculated"

    async def _save_locked(self) -> None:
        await self._store.async_save({
            "quotes": self._quotes,
            "day": self._day,
            "count": self._count,
        })


async def async_get_quote_catalog(hass) -> RouteQuoteCatalog:
    """One quote catalog per Home Assistant, shared across search profiles."""
    key = f"{DOMAIN}_quote_catalog"
    catalog = hass.data.get(key)
    if catalog is None:
        catalog = RouteQuoteCatalog(hass)
        hass.data[key] = catalog
    return catalog
