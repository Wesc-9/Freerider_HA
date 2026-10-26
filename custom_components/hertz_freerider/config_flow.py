"""Home Assistant forms for multiple watches, dates and vehicle preferences."""

from __future__ import annotations

from datetime import date

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_COUNTRIES, CONF_DATE_END, CONF_DATE_MODE, CONF_DATE_START,
    CONF_DESTINATION, CONF_DIRECTION, CONF_EVENTS, CONF_FUEL, CONF_MIN_SEATS,
    CONF_ORIGIN, CONF_SCAN_INTERVAL, CONF_SCAN_MODE, CONF_TRANSMISSION,
    CONF_VEHICLE_TYPE, CONF_WATCH_NAME, COUNTRIES, DEFAULT_POLL_MINUTES, DOMAIN,
)


def dropdown(values: list[tuple[str, str]]) -> selector.SelectSelector:
    """Use user-friendly HA choice controls."""
    return selector.SelectSelector(selector.SelectSelectorConfig(
        options=[selector.SelectOptionDict(value=key, label=label) for key, label in values],
        mode=selector.SelectSelectorMode.DROPDOWN,
    ))


def build_schema(values: dict | None = None) -> vol.Schema:
    """Build the setup/options form with optional date selection."""
    values = values or {}
    fields = {
        vol.Required(CONF_WATCH_NAME, default=values.get(CONF_WATCH_NAME, "My Freerider watch")):
            selector.TextSelector(),
        vol.Required(CONF_COUNTRIES, default=values.get(CONF_COUNTRIES, ["NO"])):
            selector.SelectSelector(selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(value=k, label=v)
                    for k, v in COUNTRIES.items()
                ],
                multiple=True, mode=selector.SelectSelectorMode.LIST,
            )),
        vol.Optional(CONF_ORIGIN, default=values.get(CONF_ORIGIN, "")):
            selector.TextSelector(),
        vol.Optional(CONF_DESTINATION, default=values.get(CONF_DESTINATION, "")):
            selector.TextSelector(),
        vol.Required(CONF_DIRECTION, default=values.get(CONF_DIRECTION, "forward")):
            dropdown([("forward", "From → To"), ("either", "Either direction")]),
        vol.Required(CONF_DATE_MODE, default=values.get(CONF_DATE_MODE, "any")):
            dropdown([("any", "Any dates"), ("single", "One date"), ("range", "Date range")]),
        vol.Required(CONF_TRANSMISSION, default=values.get(CONF_TRANSMISSION, "any")):
            dropdown([("any", "Any transmission"), ("automatic", "Automatic"), ("manual", "Manual")]),
        vol.Required(CONF_VEHICLE_TYPE, default=values.get(CONF_VEHICLE_TYPE, "any")):
            dropdown([("any", "Any vehicle"), ("car", "Car"), ("van", "Van"), ("minibus", "Minibus")]),
        vol.Required(CONF_FUEL, default=values.get(CONF_FUEL, "any")):
            dropdown([("any", "Any fuel"), ("electric", "Electric"), ("hybrid", "Hybrid"),
                      ("petrol", "Petrol"), ("diesel", "Diesel")]),
        vol.Optional(CONF_MIN_SEATS, default=values.get(CONF_MIN_SEATS, 0)):
            selector.NumberSelector(selector.NumberSelectorConfig(
                min=0, max=12, step=1, mode=selector.NumberSelectorMode.BOX,
            )),
        vol.Required(CONF_SCAN_MODE, default=values.get(CONF_SCAN_MODE, "automatic")):
            dropdown([("automatic", "Automatic background checks"), ("manual", "Manual refresh only")]),
        vol.Required(CONF_SCAN_INTERVAL, default=values.get(CONF_SCAN_INTERVAL, DEFAULT_POLL_MINUTES)):
            selector.NumberSelector(selector.NumberSelectorConfig(
                min=15, max=120, step=5, mode=selector.NumberSelectorMode.BOX,
            )),
        vol.Required(CONF_EVENTS, default=values.get(CONF_EVENTS, True)):
            selector.BooleanSelector(),
    }
    for key in (CONF_DATE_START, CONF_DATE_END):
        if values.get(key):
            fields[vol.Optional(key, default=values[key])] = selector.DateSelector()
        else:
            fields[vol.Optional(key)] = selector.DateSelector()
    return vol.Schema(fields)


def validation_error(values: dict) -> str | None:
    """Ensure the requested date filter always has well-formed dates."""
    if not values.get(CONF_COUNTRIES):
        return "missing_country"
    mode = values.get(CONF_DATE_MODE, "any")
    if mode == "any":
        return None
    try:
        start = date.fromisoformat(values[CONF_DATE_START])
        if mode == "range":
            end = date.fromisoformat(values[CONF_DATE_END])
            if end < start:
                return "end_before_start"
    except (ValueError, KeyError, TypeError):
        return "missing_date"
    return None


class FreeriderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Each config entry is one independent saved route."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Configure filter criteria and polling mode."""
        errors = {}
        if user_input is not None:
            invalid = validation_error(user_input)
            if not invalid:
                name = user_input.pop(CONF_WATCH_NAME)
                return self.async_create_entry(title=name, data=user_input)
            errors["base"] = invalid
        return self.async_show_form(
            step_id="user", data_schema=build_schema(user_input), errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Allow adjustments without reinstalling."""
        # Recent Home Assistant versions provide selclass FreeriderOptionsFlow(config_entries.OptionsFlow):
    """Edit every filter/scan setting in Home Assistant."""

    async def async_step_init(self, user_input=None):
        """Accept changed route settings."""
        errors = {}
        if user_input is not None:
            invalid = validation_error(user_input)
            if not invalid:
                name = user_input.pop(CONF_WATCH_NAME, self.config_entry.title)
                if name != self.config_entry.title:
                    self.hass.config_entries.async_update_entry(
                        self.config_entry, title=name,
                    )
                return self.async_create_entry(title="", data=user_input)
            errors["base"] = invalid
        original = {**self.config_entry.data, **self.config_entry.options}
        original[CONF_WATCH_NAME] = self.config_entry.title
        return self.async_show_form(
            step_id="init", data_schema=build_schema(user_input or original),
            errors=errors,
        )
