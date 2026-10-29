"""One optional BompengeAppen credential shared by all Freerider searches.

The key is kept in Home Assistant's private .storage (never in a watch,
device attribute, config-entry option, alert, or browser request).
"""
from __future__ import annotations

import asyncio

from homeassistant.helpers.storage import Store

from .const import CONF_TOLL_API_KEY, DOMAIN

STORE_VERSION = 1
STORE_KEY = f"{DOMAIN}_global_api_settings"


class SharedApiSettings:
    """Singleton settings shared across all configured search entries."""

    def __init__(self, hass):
        self.hass = hass
        self._store = Store(hass, STORE_VERSION, STORE_KEY)
        self._lock = asyncio.Lock()
        self._loaded = False
        self._key: str | None = None

    @property
    def api_key(self) -> str | None:
        """Read only after async_load or async_import_from_entry."""
        return self._key

    @property
    def configured(self) -> bool:
        return bool(self._key)

    async def async_load(self) -> None:
        async with self._lock:
            if self._loaded:
                return
            data = await self._store.async_load()
            if isinstance(data, dict) and isinstance(data.get("api_key"), str):
                self._key = data["api_key"].strip() or None
            self._loaded = True

    async def async_import_from_entry(self, entry) -> None:
        """Migrate old per-watch keys without deleting the chosen credential.

        The first loaded legacy key is used unless a global key already
        exists. Other legacy keys are removed from watch entries as well.
        """
        await self.async_load()
        old_key = entry.options.get(CONF_TOLL_API_KEY) or entry.data.get(CONF_TOLL_API_KEY)
        if isinstance(old_key, str) and old_key.strip():
            async with self._lock:
                if not self._key:
                    self._key = old_key.strip()
                    await self._store.async_save({"api_key": self._key})
        if CONF_TOLL_API_KEY in entry.data or CONF_TOLL_API_KEY in entry.options:
            self.hass.config_entries.async_update_entry(
                entry,
                data={k: v for k, v in entry.data.items() if k != CONF_TOLL_API_KEY},
                options={k: v for k, v in entry.options.items() if k != CONF_TOLL_API_KEY},
            )

    async def async_set_key(self, replacement: str | None, *, clear: bool = False) -> None:
        """Replace a global key or explicitly clear it, never clear on blank."""
        await self.async_load()
        normalized = replacement.strip() if isinstance(replacement, str) else ""
        if not clear and not normalized:
            return
        async with self._lock:
            new_value = None if clear else normalized
            if new_value == self._key:
                return
            self._key = new_value
            await self._store.async_save({"api_key": self._key})
        # Reflect credential availability immediately without reloading watches.
        for coordinator in self.hass.data.get(DOMAIN, {}).values():
            coordinator.async_set_updated_data(list(coordinator.data or []))


def get_shared_api_settings(hass) -> SharedApiSettings:
    """Return one shared settings instance per Home Assistant installation."""
    slot = f"{DOMAIN}_shared_api_settings"
    shared = hass.data.get(slot)
    if shared is None:
        shared = SharedApiSettings(hass)
        hass.data[slot] = shared
    return shared
