"""Availability count and inspectable listing details for each watch."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Create one sensor for this saved search."""
    async_add_entities([
        FreeriderCount(hass.data[DOMAIN][entry.entry_id], entry),
        FreeriderLastTollEstimate(hass.data[DOMAIN][entry.entry_id], entry),
    ])


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
                {**ride.as_event(), "toll_estimate": self.coordinator.toll_estimates.get(ride.key)}
                for ride in (self.coordinator.data or [])[:20]
            ],
            "total_matches": len(self.coordinator.data or []),
            "notification_target": self.coordinator.settings.get("notify_target", "off"),
            "notification_enabled": self.coordinator.settings.get("notify_enabled", True),
            "pending_notifications": len(self.coordinator.pending_notification_ids),
            "extra_costs": "Tolls may be payable. Fuel/charging may incur additional costs.",
            "tolls": "Norway: on-demand estimate from an external routing provider; no automatic batch calls.",
        }


class FreeriderLastTollEstimate(CoordinatorEntity, SensorEntity):
    """Latest manually calculated toll quote; unavailable is not zero."""

    _attr_icon = "mdi:cash"
    _attr_native_unit_of_measurement = "NOK"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{entry.title} last toll estimate"
        self._attr_unique_id = f"hertz_freerider_{entry.entry_id}_toll_nok"

    @property
    def native_value(self):
        """Return the last amount, if a user explicitly requested one."""
        quote = self.coordinator.last_toll_estimate
        return quote.get("amount_nok") if quote else None

    @property
    def extra_state_attributes(self):
        """Make charging assumptions and station details visible in HA."""
        return self.coordinator.last_toll_estimate or {
            "status": "not_calculated",
            "info": "Use the toll estimate button or hertz_freerider.estimate_toll service.",
            "fuel_charging_note": "Fuel/charging costs may apply.",
        }
