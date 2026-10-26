"""Availability count and inspectable listing details for each watch."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Create one sensor for this saved search."""
    async_add_entities([FreeriderCount(hass.data[DOMAIN][entry.entry_id], entry)])


class FreeriderCount(CoordinatorEntity, SensorEntity):
    """Matched real offers; source failures are 'unavailable', not zero."""

    _attr_icon = "mdi:car-multiple"
    _attr_native_unit_of_measurement = "rides"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{entry.title} matching rides"
        self._attr_unique_id = f"hertz_freerider_{entry.entry_id}_count"

    @property
    def native_value(self):
        """Count matches only following a successful live data fetch."""
        return len(self.coordinator.data or [])

    @property
    def extra_state_attributes(self):
        """Expose a small list of actionable matches without bloating state."""
        return {
            "filters": self.coordinator.settings,
            "source_errors": self.coordinator.last_source_errors,
            "rides": [
                ride.as_event() for ride in (self.coordinator.data or [])[:20]
            ],
            "total_matches": len(self.coordinator.data or []),
        }
