"""Toggle Freerider HA alerts from the Home Assistant entity screen."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError

from .device import watch_device_info
from .const import DOMAIN, CONF_NOTIFY_TARGET, CONF_NOTIFY_ENABLED
from .notifications import TARGET_OFF


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Create one alerts switch per saved search."""
    async_add_entities([FreeriderAlertSwitch(entry)])


class FreeriderAlertSwitch(SwitchEntity):
    """Enable or disable notifications while keeping the chosen phone."""

    _attr_icon = "mdi:bell-ring"

    def __init__(self, entry) -> None:
        self._entry = entry
        self._attr_device_info = watch_device_info(entry)
        self._attr_name = f"{entry.title} new car alerts"
        self._attr_unique_id = f"hertz_freerider_{entry.entry_id}_new_car_alerts"

    @property
    def is_on(self) -> bool:
        """No recipient selected means alerts cannot be enabled."""
        cfg = {**self._entry.data, **self._entry.options}
        target = cfg.get(CONF_NOTIFY_TARGET, TARGET_OFF)
        return target != TARGET_OFF and bool(cfg.get(CONF_NOTIFY_ENABLED, True))

    async def async_turn_on(self, **kwargs) -> None:
        """Require a recipient before switching on."""
        cfg = {**self._entry.data, **self._entry.options}
        if cfg.get(CONF_NOTIFY_TARGET, TARGET_OFF) == TARGET_OFF:
            raise HomeAssistantError(
                "Select a mobile phone in Freerider HA → Configure → "
                "Automatic checks and notifications first."
            )
        self.hass.config_entries.async_update_entry(
            self._entry,
            options={**self._entry.options, CONF_NOTIFY_ENABLED: True},
        )

    async def async_turn_off(self, **kwargs) -> None:
        """Disable alerts without deleting previously chosen phone."""
        self.hass.config_entries.async_update_entry(
            self._entry,
            options={**self._entry.options, CONF_NOTIFY_ENABLED: False},
        )
