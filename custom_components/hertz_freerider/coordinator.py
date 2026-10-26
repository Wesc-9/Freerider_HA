"""Poll source adapters, maintain search results and emit new-offer events."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_COUNTRIES, CONF_EVENTS, CONF_SCAN_INTERVAL, CONF_SCAN_MODE,
    DEFAULT_POLL_MINUTES, DOMAIN, EVENT_NEW_RIDE,
)
from .filters import Ride, filter_rides
from .source import async_fetch_country

_LOGGER = logging.getLogger(__name__)
MAX_REMEMBERED = 1500


class FreeriderCoordinator(DataUpdateCoordinator[list[Ride]]):
    """One independent saved route, editable through integration options."""

    def __init__(self, hass, entry) -> None:
        self.entry = entry
        self.settings = {**entry.data, **entry.options}
        self.seen_store = Store(hass, 1, f"{DOMAIN}_seen_{entry.entry_id}")
        self.seen_ids: list[str] | None = None
        self.last_source_errors: dict[str, str] = {}
        automatic = self.settings.get(CONF_SCAN_MODE, "automatic") == "automatic"
        interval = max(15, min(120, int(self.settings.get(
            CONF_SCAN_INTERVAL, DEFAULT_POLL_MINUTES
        ))))
        super().__init__(
            hass,
            _LOGGER,
            name=f"Freerider {entry.title}",
            update_interval=timedelta(minutes=interval) if automatic else None,
        )

    async def async_initialize(self) -> None:
        """Load recent ID history before performing the first refresh."""
        loaded = await self.seen_store.async_load()
        if isinstance(loaded, dict) and isinstance(loaded.get("ids"), list):
            self.seen_ids = [str(key) for key in loaded["ids"]][-MAX_REMEMBERED:]

    async def _async_update_data(self) -> list[Ride]:
        countries = self.settings.get(CONF_COUNTRIES, ["NO"])
        results = await asyncio.gather(
            *(async_fetch_country(self.hass, country) for country in countries),
            return_exceptions=True,
        )
        valid: list[Ride] = []
        succeeded = False
        self.last_source_errors = {}
        for country, result in zip(countries, results):
            if isinstance(result, BaseException):
                self.last_source_errors[country] = str(result)
            elif isinstance(result, list):
                succeeded = True
                valid.extend(result)
            else:
                self.last_source_errors[country] = "Unexpected adapter response"

        # Failed providers must never be reported as zero available cars.
        if not succeeded:
            raise UpdateFailed("; ".join(
                f"{c}: {err}" for c, err in self.last_source_errors.items()
            ) or "No active Freerider source")

        # One offer can be exposed by several provider views: de-duplicate IDs.
        unique = {ride.key: ride for ride in valid}
        matched = filter_rides(list(unique.values()), self.settings)
        await self._remember_and_notify(matched)
        return matched

    async def _remember_and_notify(self, matched: list[Ride]) -> None:
        new_ids = {ride.key for ride in matched}
        previous = set(self.seen_ids) if self.seen_ids is not None else None
        if previous is not None and self.settings.get(CONF_EVENTS, True):
            for ride in matched:
                if ride.key not in previous:
                    self.hass.bus.async_fire(EVENT_NEW_RIDE, {
                        "entry_id": self.entry.entry_id,
                        "watch_name": self.entry.title,
                        **ride.as_event(),
                    })
        # First successful update establishes a baseline without flooding alerts.
        merged = list(dict.fromkeys([
            *(self.seen_ids or []), *(ride.key for ride in matched)
        ]))[-MAX_REMEMBERED:]
        if merged != self.seen_ids:
            self.seen_ids = merged
            await self.seen_store.async_save({"ids": merged})
