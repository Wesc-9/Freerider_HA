"""Toggle Freerider HA alerts from the Home Assistant entity screen."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError

from .device import watch_device_info
from .trip_profiles import all_watch_profiles, update_watch_setting
from .const import DOMAIN, CONF_NOTIFY_TARGET, CONF_NOTIFY_ENABLED, CONF_SEARCH_ACTIVE
from .notifications import TARGET_OFF
from .search_mode import search_active


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Independent pause/alert controls for every saved trip."""
    for profile in all_watch_profiles(entry):
        entities = [
            FreeriderSearchSwitch(profile),
            FreeriderAlertSwitch(profile),
        ]
        subentry_id = getattr(profile, "subentry_id", None)
        if subentry_id is not None:
            async_add_entities(entities, config_subentry_id=subentry_id)
        else:
            async_add_entities(entities)


class FreeriderSearchSwitch(SwitchEntity):
    """Pause or resume an individual saved watch, preserving all settings.

    This is independent of Home Assistant's native config-entry Disable
    action and provides a practical fallback when that action fails.
    """

    _attr_icon = "mdi:radar"

    def __init__(self, entry) -> None:
        self._entry = entry
        self._attr_device_info = watch_device_info(entry)
        self._attr_name = f"{entry.title} search active"
        self._attr_unique_id = f"hertz_freerider_{entry.entry_id}_search_active"

    @property
    def is_on(self) -> bool:
        return search_active({**self._entry.data, **self._entry.options})

    async def async_turn_on(self, **kwargs) -> None:
        update_watch_setting(self.hass, self._entry, CONF_SEARCH_ACTIVE, True)

    async def async_turn_off(self, **kwargs) -> None:
        update_watch_setting(self.hass, self._entry, CONF_SEARCH_ACTIVE, False)


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
                "Velg først mottakeren under Freerider HA → Konfigurer → "
                "Steder, dato og varsler."
            )
        update_watch_setting(self.hass, self._entry, CONF_NOTIFY_ENABLED, True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable alerts without deleting previously chosen phone."""
        update_watch_setting(self.hass, self._entry, CONF_NOTIFY_ENABLED, False)
