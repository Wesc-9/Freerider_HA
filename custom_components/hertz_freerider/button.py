"""On-demand Freerider refresh for each saved route."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError
from .tolls import TollLookupError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Add a refresh action even if the live source is currently unavailable."""
    async_add_entities([
        FreeriderRefresh(hass.data[DOMAIN][entry.entry_id], entry),
        FreeriderEstimateFirstToll(hass.data[DOMAIN][entry.entry_id], entry),
        FreeriderTestNotification(hass.data[DOMAIN][entry.entry_id], entry),
    ])


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


class FreeriderEstimateFirstToll(CoordinatorEntity, ButtonEntity):
    """On-demand toll lookup for the first matching eligible Norwegian ride."""

    _attr_icon = "mdi:cash-multiple"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{entry.title} estimate toll for first match"
        self._attr_unique_id = f"hertz_freerider_{entry.entry_id}_estimate_toll"

    @property
    def available(self) -> bool:
        """Requires a successful listing update and at least one result."""
        return bool(self.coordinator.last_update_success and self.coordinator.data)

    async def async_press(self) -> None:
        """Estimate toll on the first sorted matching route only."""
        if not self.coordinator.data:
            raise HomeAssistantError("No matching Freerider routes available")
        try:
            await self.coordinator.async_calculate_toll(self.coordinator.data[0].key)
        except TollLookupError as exc:
            raise HomeAssistantError(str(exc)) from exc


class FreeriderTestNotification(CoordinatorEntity, ButtonEntity):
    """Send a clearly marked test alert to the selected mobile app."""

    _attr_icon = "mdi:bell-check"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{entry.title} test notification"
        self._attr_unique_id = f"hertz_freerider_{entry.entry_id}_test_notification"

    @property
    def available(self) -> bool:
        """Sending a test alert does not depend on Freerider feed status."""
        return True

    async def async_press(self) -> None:
        """Allow the user to verify alert delivery without a live car."""
        try:
            sent = await self.coordinator.async_send_test_notification()
        except Exception as exc:
            raise HomeAssistantError(
                "Test notification failed. Check the selected device in Configure."
            ) from exc
        if not sent:
            raise HomeAssistantError(
                "Choose a phone or Home Assistant notifications in Configure → "
                "Automatic checks and notifications before sending a test."
            )
