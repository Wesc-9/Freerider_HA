"""Hertz Freerider Home Assistant integration (alpha foundation)."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, SERVICE_REFRESH
from .coordinator import FreeriderCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "button"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register a safe manual refresh action for all or one saved watch."""

    async def refresh(call: ServiceCall) -> None:
        entry_id = call.data.get("entry_id")
        coordinators = hass.data.get(DOMAIN, {})
        if entry_id:
            coordinators = {
                entry_id: coordinators[entry_id]
            } if entry_id in coordinators else {}
        for coordinator in coordinators.values():
            await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN, SERVICE_REFRESH, refresh,
        schema=vol.Schema({vol.Optional("entry_id"): str}),
    )
    return True


async def async_setup_entry(hass, entry) -> bool:
    """Set up one watch. An unavailable source must not block configuration."""
    coordinator = FreeriderCoordinator(hass, entry)
    await coordinator.async_initialize()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    # async_refresh records source failure but does not pretend there are 0 offers.
    await coordinator.async_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_reload_entry(hass, entry) -> None:
    """Reload after editing date, vehicle, country and polling options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry) -> bool:
    """Cleanly unload an individual route profile."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        entry.async_unload()
    return ok
