"""Poll source adapters, maintain search results and emit new-offer events."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from time import monotonic
import logging

from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_COUNTRIES, CONF_EVENTS, CONF_SCAN_INTERVAL, CONF_SCAN_MODE,
    DEFAULT_POLL_MINUTES, DOMAIN, EVENT_NEW_RIDE, CONF_NOTIFY_TARGET,
)
from .filters import Ride, filter_rides
from .source import async_fetch_country
from .notifications import (
    TARGET_OFF, async_send_notification, notification_content, test_notification_content,
)
from .station_catalog import async_get_station_catalog
from .tolls import async_estimate_toll, TollLookupError

_LOGGER = logging.getLogger(__name__)
MAX_REMEMBERED = 1500


class FreeriderCoordinator(DataUpdateCoordinator[list[Ride]]):
    """One independent saved route, editable through integration options."""

    def __init__(self, hass, entry) -> None:
        self.entry = entry
        self.settings = {**entry.data, **entry.options}
        self.seen_store = Store(hass, 1, f"{DOMAIN}_seen_{entry.entry_id}")
        self.seen_ids: list[str] | None = None
        self.pending_notification_ids: list[str] = []
        self.last_source_errors: dict[str, str] = {}
        self.toll_estimates: dict[str, dict] = {}
        self._toll_cache: dict[tuple[str, str], tuple[float, dict]] = {}
        self.last_toll_estimate: dict | None = None
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
            previous_pending = loaded.get("pending", [])
            if isinstance(previous_pending, list):
                self.pending_notification_ids = [
                    key for key in previous_pending if isinstance(key, str)
                ][-80:]

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

        # Learn stations from ALL successfully fetched routes, not only those
        # matching this particular saved search. The catalog survives restarts
        # and is shared between every Freerider profile in this HA instance.
        catalog = await async_get_station_catalog(self.hass)
        for country, result in zip(countries, results):
            if isinstance(result, list):
                await catalog.async_learn(country, result)

        # One offer can be exposed by several provider views: de-duplicate IDs.
        unique = {ride.key: ride for ride in valid}
        matched = filter_rides(list(unique.values()), self.settings)
        await self._remember_and_notify(matched)
        return matched

    async def _remember_and_notify(self, matched: list[Ride]) -> None:
        """Emit events and deliver chosen mobile push for genuinely new rides.

        The very first successful feed scan establishes a baseline, rather
        than notifying about every already available car. Failed mobile push
        attempts are remembered and retried on the next successful scan while
        the matching ride is still available.
        """
        previous = set(self.seen_ids) if self.seen_ids is not None else None
        old_pending = list(self.pending_notification_ids)
        new_rides = [ride for ride in matched if previous is not None and ride.key not in previous]

        if self.settings.get(CONF_EVENTS, True):
            for ride in new_rides:
                self.hass.bus.async_fire(EVENT_NEW_RIDE, {
                    "entry_id": self.entry.entry_id,
                    "watch_name": self.entry.title,
                    **ride.as_event(),
                })

        target = self.settings.get(CONF_NOTIFY_TARGET, TARGET_OFF)
        if target != TARGET_OFF and previous is not None:
            queued = set(self.pending_notification_ids)
            next_ids = {ride.key for ride in new_rides} | queued
            pending: list[str] = []
            sent_count = 0
            for ride in matched:
                if ride.key not in next_ids:
                    continue
                if sent_count >= 8:
                    pending.append(ride.key)
                    continue
                sent_count += 1
                try:
                    delivered = await async_send_notification(
                        self.hass, target,
                        notification_content(
                            ride, self.entry.title, self.hass.config.language,
                        ),
                    )
                except Exception:
                    # An unavailable phone must never break the main sensor.
                    _LOGGER.exception(
                        "Freerider HA could not send a mobile notification for %s",
                        ride.key,
                    )
                    delivered = False
                if not delivered:
                    pending.append(ride.key)
            self.pending_notification_ids = pending[-80:]
        else:
            self.pending_notification_ids = []

        merged = list(dict.fromkeys([
            *(self.seen_ids or []), *(ride.key for ride in matched),
        ]))[-MAX_REMEMBERED:]
        if merged != self.seen_ids or old_pending != self.pending_notification_ids:
            self.seen_ids = merged
            await self.seen_store.async_save({
                "ids": merged,
                "pending": self.pending_notification_ids,
            })

    async def async_send_test_notification(self) -> bool:
        """User-triggered validation of the selected mobile destination."""
        target = self.settings.get(CONF_NOTIFY_TARGET, TARGET_OFF)
        if not target or target == TARGET_OFF:
            return False
        return await async_send_notification(
            self.hass, target,
            test_notification_content(self.entry.title, self.hass.config.language),
        )

    async def async_calculate_toll(
        self, ride_id: str, start_time: str | None = None
    ) -> dict:
        """Run a manually requested toll lookup for an exact matching ride."""
        match = next((ride for ride in (self.data or []) if ride.key == ride_id), None)
        if match is None:
            raise TollLookupError("Ride ID is not in the current matching results")
        key = (ride_id, start_time or "")
        stored = self._toll_cache.get(key)
        if stored and monotonic() - stored[0] < 3600:
            estimate = dict(stored[1])
        else:
            estimate = await async_estimate_toll(self.hass, match, start_time)
            self._toll_cache[key] = (monotonic(), dict(estimate))
            # Limit in-memory cache size (quotas belong to external provider).
            if len(self._toll_cache) > 100:
                self._toll_cache.pop(next(iter(self._toll_cache)))

        self.toll_estimates[ride_id] = estimate
        self.last_toll_estimate = estimate
        # Notify Home Assistant sensors; do not emit a new-car event for a toll
        # calculation, which would otherwise trigger spurious push notifications.
        self.async_set_updated_data(list(self.data or []))
        return estimate
