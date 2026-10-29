"""Freerider HA: unofficial route monitoring, notifications and optional UI."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, SERVICE_REFRESH
from .tolls import TollLookupError
from .api_settings import get_shared_api_settings
from .coordinator import FreeriderCoordinator
from .dashboard import async_setup_dashboard
from .trip_profiles import all_watch_profiles

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "button", "switch"]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register services and expose the optional results dashboard card."""
    await async_setup_dashboard(hass)

    async def refresh(call: ServiceCall) -> None:
        entry_id = call.data.get("entry_id")
        coordinators = hass.data.get(DOMAIN, {})
        if entry_id:
            coordinators = {
                entry_id: coordinators[entry_id]
            } if entry_id in coordinators else {}
        for coordinator in coordinators.values():
            await coordinator.async_force_refresh()

    hass.services.async_register(
        DOMAIN, SERVICE_REFRESH, refresh,
        schema=vol.Schema({vol.Optional("entry_id"): str}),
    )
    async def estimate_toll(call: ServiceCall) -> None:
        """Manual toll estimate for the exact route in a saved watch."""
        entry_id = call.data["entry_id"]
        ride_id = call.data["ride_id"]
        coordinator = hass.data.get(DOMAIN, {}).get(entry_id)
        if coordinator is None:
            raise HomeAssistantError("Freerider watch entry not found")
        try:
            await coordinator.async_calculate_toll(
                ride_id, call.data.get("start_time")
            )
        except TollLookupError as exc:
            raise HomeAssistantError(str(exc)) from exc

    hass.services.async_register(
        DOMAIN, "estimate_toll", estimate_toll,
        schema=vol.Schema({
            vol.Required("entry_id"): str,
            vol.Required("ride_id"): str,
            vol.Optional("start_time"): str,
        }),
    )
    async def set_favorite(call: ServiceCall) -> None:
        """Manage an offer bookmark locally, never make a booking."""
        entry_id=call.data["entry_id"]
        coordinator=hass.data.get(DOMAIN,{}).get(entry_id)
        if coordinator is None:
            raise HomeAssistantError("Unknown Freerider search")
        try:
            await coordinator.async_set_favorite(
                call.data["ride_id"],call.data["favorite"],
            )
        except ValueError as exc:
            raise HomeAssistantError(str(exc)) from exc

    hass.services.async_register(
        DOMAIN,"set_favorite",set_favorite,
        schema=vol.Schema({
            vol.Required("entry_id"):str,
            vol.Required("ride_id"):str,
            vol.Required("favorite"):bool,
        }),
    )
    return True


async def async_setup_entry(hass, entry) -> bool:
    """Set up one watch. An unavailable source must not block configuration."""
    # Move legacy per-search credentials into one private global setting.
    await get_shared_api_settings(hass).async_import_from_entry(entry)
    # A modern parent holds trips as subentries. Legacy entries still represent
    # one watch and keep their original entity IDs and saved search history.
    owned_ids = []
    coordinators = hass.data.setdefault(DOMAIN, {})
    for profile in all_watch_profiles(entry):
        coordinator = FreeriderCoordinator(hass, profile)
        await coordinator.async_initialize()
        coordinators[profile.entry_id] = coordinator
        owned_ids.append(profile.entry_id)
        # A source error must not prevent the other trips from loading.
        await coordinator.async_refresh()
    hass.data.setdefault(f"{DOMAIN}_owned_profiles", {})[entry.entry_id] = owned_ids
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_reload_entry(hass, entry) -> None:
    """Reload after editing date, vehicle, country and polling options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry) -> bool:
    """Support Home Assistant's native Disable and Reload actions.

    Home Assistant owns ConfigEntry.async_unload() and runs all callbacks
    registered with entry.async_on_unload() *after* this function returns.
    Calling entry.async_unload() here is erroneous and can recursively try
    to unload the same entry (or raise TypeError for the missing hass arg).
    """
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        owned = hass.data.get(f"{DOMAIN}_owned_profiles", {}).pop(
            entry.entry_id,
            [entry.entry_id] if entry.entry_id in hass.data.get(DOMAIN, {}) else [],
        )
        for profile_id in owned:
            coordinator = hass.data.get(DOMAIN, {}).pop(profile_id, None)
            # Cancel periodic checks: HA owns platform listeners and coordinator
            # schedules must not outlive the corresponding trip.
            if coordinator is not None:
                await coordinator.async_shutdown()
    return ok
