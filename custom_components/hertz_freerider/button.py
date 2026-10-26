"""On-demand Freerider refresh for each saved route."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Add a refresh action even if the live source is currently unavailable."""
    async_add_entities([FreeriderRefresh(hass.data[DOMAIN][entry.entry_id], entry)])


class FreeriderRefresh(CoordinatorEntity, ButtonEntity):
    """Refresh offers without changing scanning preferences."""

    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{entry.title} refresh listings"
        self._attr_unique_id = f"hertz_freerider_{entry.entry_id}_refresh"

    @property
    def available(self) -> bool:
        """Always permit manual retries after an adapter/network error."""
        return True

    async def async_press(self) -> None:
        """Request immediate update from enabled country adapters."""
        await self.coordinator.async_request_refresh()
