"""Simple multi-step Home Assistant setup, bilingual and station-aware.

The normal Home Assistant theme controls light/dark appearance; custom
integrations do not inject custom CSS into native setup dialogs.
"""

from __future__ import annotations

import asyncio
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
from .filters import station_candidates, place_values
from .source import async_fetch_country


def select(options: list[str], translation_key: str):
    """Dropdown with localized values from strings.json and translations."""
    return selector.SelectSelector(selector.SelectSelectorConfig(
        options=options,
        mode=selector.SelectSelectorMode.DROPDOWN,
        translation_key=translation_key,
    ))


def countries_schema(values: dict | None = None) -> vol.Schema:
    """Keep the first screen short: name plus source country selection."""
    values = values or {}
    return vol.Schema({
        vol.Required(CONF_WATCH_NAME, default=values.get(CONF_WATCH_NAME, "Freerider")):
            selector.TextSelector(),
        vol.Required(CONF_COUNTRIES, default=[
            country.lower() for country in values.get(CONF_COUNTRIES, ["NO"])
        ]):
            selector.SelectSelector(selector.SelectSelectorConfig(
                options=[country.lower() for country in COUNTRIES],
                multiple=True,
                mode=selector.SelectSelectorMode.LIST,
                translation_key="countries",
            )),
    })


def _place_selector(names: list[str]):
    """One searchable multi-select with native text entry and chips.

    HA's SelectSelector supports multiple=True and custom_value=True.  No
    custom frontend is needed; submitted data is a list of chosen places.
    """
    return selector.SelectSelector(selector.SelectSelectorConfig(
        options=names,
        multiple=True,
        custom_value=True,
        mode=selector.SelectSelectorMode.DROPDOWN,
        sort=True,
    ))


def route_schema(values: dict | None, stations: list[str]) -> vol.Schema:
    """Show departure, destination and travel dates together."""
    values = values or {}
    fields = {}
    for key in (CONF_ORIGIN, CONF_DESTINATION):
        places = place_values(values.get(key))
        field = vol.Optional(key, default=places) if places else vol.Optional(key)
        fields[field] = _place_selector(stations)
    fields[vol.Required(
        CONF_DIRECTION, default=values.get(CONF_DIRECTION, "forward")
    )] = select(["forward", "either"], "direction")
    for key in (CONF_DATE_START, CONF_DATE_END):
        if values.get(key):
            fields[vol.Optional(key, default=values[key])] = selector.DateSelector()
        else:
            fields[vol.Optional(key)] = selector.DateSelector()
    return vol.Schema(fields)


def route_dates(payload: dict) -> dict:
    """Infer all/single/range from two optional dates on the route screen."""
    start = payload.get(CONF_DATE_START) or None
    end = payload.get(CONF_DATE_END) or None
    return {
        CONF_DATE_MODE: "range" if start and end else "single" if start else "any",
        CONF_DATE_START: start,
        CONF_DATE_END: end,
    }




def date_mode_schema(values: dict | None = None) -> vol.Schema:
    values = values or {}
    return vol.Schema({
        vol.Required(CONF_DATE_MODE, default=values.get(CONF_DATE_MODE, "any")):
            select(["any", "single", "range"], "date_mode"),
    })


def date_window_schema(mode: str, values: dict | None = None) -> vol.Schema:
    values = values or {}
    fields = {
        vol.Required(CONF_DATE_START, default=values[CONF_DATE_START])
        if values.get(CONF_DATE_START)
        else vol.Required(CONF_DATE_START): selector.DateSelector(),
    }
    if mode == "range":
        fields[
            vol.Required(CONF_DATE_END, default=values[CONF_DATE_END])
            if values.get(CONF_DATE_END)
            else vol.Required(CONF_DATE_END)
        ] = selector.DateSelector()
    return vol.Schema(fields)


def vehicle_schema(values: dict | None = None) -> vol.Schema:
    values = values or {}
    return vol.Schema({
        vol.Required(CONF_TRANSMISSION, default=values.get(CONF_TRANSMISSION, "any")):
            select(["any", "automatic", "manual"], "transmission"),
        vol.Required(CONF_VEHICLE_TYPE, default=values.get(CONF_VEHICLE_TYPE, "any")):
            select(["any", "car", "van", "minibus"], "vehicle_type"),
        vol.Required(CONF_FUEL, default=values.get(CONF_FUEL, "any")):
            select(["any", "electric", "hybrid", "petrol", "diesel"], "fuel"),
        vol.Optional(CONF_MIN_SEATS, default=values.get(CONF_MIN_SEATS, 0)):
            selector.NumberSelector(selector.NumberSelectorConfig(
                min=0, max=12, step=1, mode=selector.NumberSelectorMode.BOX,
            )),
    })


def updates_schema(values: dict | None = None) -> vol.Schema:
    values = values or {}
    return vol.Schema({
        vol.Required(CONF_SCAN_MODE, default=values.get(CONF_SCAN_MODE, "automatic")):
            select(["automatic", "manual"], "scan_mode"),
        vol.Required(CONF_SCAN_INTERVAL, default=values.get(
            CONF_SCAN_INTERVAL, DEFAULT_POLL_MINUTES,
        )):
            selector.NumberSelector(selector.NumberSelectorConfig(
                min=15, max=120, step=5, mode=selector.NumberSelectorMode.BOX,
            )),
        vol.Required(CONF_EVENTS, default=values.get(CONF_EVENTS, True)):
            selector.BooleanSelector(),
    })


def validation_error(values: dict) -> str | None:
    """Validate country availability and date ordering."""
    countries = values.get(CONF_COUNTRIES)
    if countries is not None:
        if not countries:
            return "missing_country"
        # Denmark is displayed as upcoming, not offered as an operational feed.
        if not (set(countries) & {"NO", "SE"}):
            return "country_not_ready"
    mode = values.get(CONF_DATE_MODE, "any")
    if mode not in ("single", "range"):
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


async def async_station_suggestions(hass, countries: list[str]) -> list[str]:
    """Fetch distinct published stations, ignoring provider failures.

    This is a convenience hint only: a missing station must remain searchable
    via the free-text option. Denmark has no verified listing adapter.
    """
    active = [country for country in countries if country in ("NO", "SE")]
    results = await asyncio.gather(
        *(async_fetch_country(hass, country) for country in active),
        return_exceptions=True,
    )
    rides = [
        ride for result in results if isinstance(result, list)
        for ride in result
    ]
    return station_candidates(rides)


class FreeriderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Short guided setup with free-text-compatible station suggestions."""

    VERSION = 1

    def __init__(self) -> None:
        self._draft: dict = {}
        self._stations: list[str] | None = None

    async def async_step_user(self, user_input=None):
        """Page one: name and countries."""
        errors = {}
        if user_input is not None:
            user_input = {
                **user_input,
                CONF_COUNTRIES: [
                    country.upper() for country in user_input.get(CONF_COUNTRIES, [])
                ],
            }
            invalid = validation_error(user_input)
            if invalid is None:
                self._draft.update(user_input)
                return await self.async_step_route()
            errors["base"] = invalid
        return self.async_show_form(
            step_id="user", data_schema=countries_schema(user_input), errors=errors,
        )

    async def async_step_route(self, user_input=None):
        """Page two: multi-station route and optional date range in one form."""
        errors = {}
        if user_input is not None:
            candidate = {
                **self._draft, **user_input,
                CONF_ORIGIN: place_values(user_input.get(CONF_ORIGIN)),
                CONF_DESTINATION: place_values(user_input.get(CONF_DESTINATION)),
                **route_dates(user_input),
            }
            invalid = validation_error(candidate)
            if not invalid and user_input.get(CONF_DATE_END) and not user_input.get(CONF_DATE_START):
                invalid = "missing_date"
            if not invalid:
                self._draft = candidate
                return self._finish()
            errors["base"] = invalid
        if self._stations is None:
            self._stations = await async_station_suggestions(
                self.hass, self._draft.get(CONF_COUNTRIES, ["NO"])
            )
        return self.async_show_form(
            step_id="route",
            data_schema=route_schema(
                {**self._draft, **(user_input or {})}, self._stations,
            ),
            errors=errors,
        )



    async def async_step_date(self, user_input=None):
        """Page three: all dates by default, optional single day or range."""
        if user_input is not None:
            self._draft.update(user_input)
            if user_input[CONF_DATE_MODE] == "any":
                self._draft.pop(CONF_DATE_START, None)
                self._draft.pop(CONF_DATE_END, None)
                return self._finish()
            return await self.async_step_date_window()
        return self.async_show_form(
            step_id="date", data_schema=date_mode_schema(self._draft),
        )

    async def async_step_date_window(self, user_input=None):
        """Only display date fields when needed."""
        errors = {}
        if user_input is not None:
            candidate = {**self._draft, **user_input}
            invalid = validation_error(candidate)
            if invalid is None:
                self._draft.update(user_input)
                if self._draft[CONF_DATE_MODE] == "single":
                    self._draft.pop(CONF_DATE_END, None)
                return self._finish()
            errors["base"] = invalid
        return self.async_show_form(
            step_id="date_window",
            data_schema=date_window_schema(self._draft[CONF_DATE_MODE], {
                **self._draft, **(user_input or {}),
            }),
            errors=errors,
        )

    def _finish(self):
        """Create one saved watch using sensible, editable defaults."""
        fields = {
            CONF_TRANSMISSION: "any",
            CONF_VEHICLE_TYPE: "any",
            CONF_FUEL: "any",
            CONF_MIN_SEATS: 0,
            CONF_SCAN_MODE: "automatic",
            CONF_SCAN_INTERVAL: DEFAULT_POLL_MINUTES,
            CONF_EVENTS: True,
        }
        fields.update(self._draft)
        title = fields.pop(CONF_WATCH_NAME, "Freerider")
        return self.async_create_entry(title=title, data=fields)

    @staticmethod
    def async_get_options_flow(config_entry):
        """Group optional settings instead of presenting one giant form."""
        return FreeriderOptionsFlow()


class FreeriderOptionsFlow(config_entries.OptionsFlow):
    """Small, editable screens for route, date, vehicle and notifications."""

    def __init__(self) -> None:
        self._stations: list[str] | None = None
        self._date_mode: str = "any"

    def _settings(self) -> dict:
        return {**self.config_entry.data, **self.config_entry.options}

    async def async_step_init(self, user_input=None):
        """Choose which part of the configuration to change."""
        return self.async_show_menu(
            step_id="init", menu_options=["route", "dates", "filters", "updates"],
        )

    async def async_step_route(self, user_input=None):
        """Edit saved station groups and dates without recreating a watch."""
        errors = {}
        current = self._settings()
        if user_input is not None:
            user_input = {
                **user_input,
                CONF_COUNTRIES: [
                    country.upper() for country in user_input.get(CONF_COUNTRIES, [])
                ],
                CONF_ORIGIN: place_values(user_input.get(CONF_ORIGIN)),
                CONF_DESTINATION: place_values(user_input.get(CONF_DESTINATION)),
                **route_dates(user_input),
            }
            invalid = validation_error(user_input)
            if not invalid and user_input.get(CONF_DATE_END) and not user_input.get(CONF_DATE_START):
                invalid = "missing_date"
            if invalid is None:
                title = user_input.pop(CONF_WATCH_NAME, self.config_entry.title)
                if title != self.config_entry.title:
                    self.hass.config_entries.async_update_entry(
                        self.config_entry, title=title,
                    )
                return self.async_create_entry(title="", data={
                    **self.config_entry.options, **user_input,
                })
            errors["base"] = invalid

        selected = (user_input or current).get(CONF_COUNTRIES, ["NO"])
        self._stations = await async_station_suggestions(self.hass, selected)
        values = {**current, **(user_input or {}), CONF_WATCH_NAME: self.config_entry.title}
        fields = dict(countries_schema(values).schema)
        fields.update(route_schema(values, self._stations).schema)
        return self.async_show_form(
            step_id="route", data_schema=vol.Schema(fields), errors=errors,
        )



    async def async_step_dates(self, user_input=None):
        """Choose any day, a single day, or a date window."""
        if user_input is not None:
            self._date_mode = user_input[CONF_DATE_MODE]
            if self._date_mode == "any":
                return self.async_create_entry(title="", data={
                    **self.config_entry.options,
                    CONF_DATE_MODE: "any",
                    CONF_DATE_START: None,
                    CONF_DATE_END: None,
                })
            return await self.async_step_date_window()
        return self.async_show_form(
            step_id="dates", data_schema=date_mode_schema(self._settings()),
        )

    async def async_step_date_window(self, user_input=None):
        """Ask for only the relevant date fields."""
        errors = {}
        if user_input is not None:
            candidate = {**user_input, CONF_DATE_MODE: self._date_mode}
            invalid = validation_error(candidate)
            if invalid is None:
                return self.async_create_entry(title="", data={
                    **self.config_entry.options,
                    CONF_DATE_MODE: self._date_mode,
                    CONF_DATE_START: user_input[CONF_DATE_START],
                    CONF_DATE_END: user_input.get(CONF_DATE_END)
                    if self._date_mode == "range" else None,
                })
            errors["base"] = invalid
        current = {**self._settings(), **(user_input or {})}
        return self.async_show_form(
            step_id="date_window",
            data_schema=date_window_schema(self._date_mode, current),
            errors=errors,
        )

    async def async_step_filters(self, user_input=None):
        """Optional advanced vehicle filters."""
        if user_input is not None:
            return self.async_create_entry(title="", data={
                **self.config_entry.options, **user_input,
            })
        return self.async_show_form(
            step_id="filters", data_schema=vehicle_schema(self._settings()),
        )

    async def async_step_updates(self, user_input=None):
        """Optional polling/notification event configuration."""
        if user_input is not None:
            return self.async_create_entry(title="", data={
                **self.config_entry.options, **user_input,
            })
        return self.async_show_form(
            step_id="updates", data_schema=updates_schema(self._settings()),
        )
