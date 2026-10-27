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
    CONF_ORIGIN, CONF_SCAN_INTERVAL, CONF_SCAN_MODE, CONF_NOTIFY_TARGET, CONF_NOTIFY_ENABLED, CONF_TOLL_IN_NOTIFICATIONS, CONF_TRANSMISSION,
    CONF_VEHICLE_TYPE, CONF_WATCH_NAME, COUNTRIES, DEFAULT_POLL_MINUTES, DOMAIN,
    CONF_MODEL_INCLUDE, CONF_MODEL_EXCLUDE, CONF_RADIUS_KM,
    CONF_ALERT_EXISTING, CONF_ALERT_UPDATES, CONF_FUEL_USAGE, CONF_FUEL_PRICE,
    CONF_ELECTRIC_USAGE, CONF_ELECTRIC_PRICE, CONF_SEARCH_ACTIVE, CONF_ALL_DATES,
    CONF_SORT_BY, CONF_QUIET_START, CONF_QUIET_END, CONF_QUIET_URGENT, CONF_MAX_TOLL, CONF_ONLY_FEASIBLE,
)
from .filters import station_candidates, place_values
from .source import async_fetch_country
from .notifications import notification_targets, TARGET_OFF
from .station_catalog import async_get_station_catalog
from .search_enhancements import distance_km
from .radius_settings import validate_radius_settings, radius_default


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


def all_dates_default(values: dict) -> bool:
    """Maintain old searches that may have chosen a date period."""
    if CONF_ALL_DATES in values:
        return bool(values[CONF_ALL_DATES])
    return values.get(CONF_DATE_MODE, "any") == "any"


def all_dates_fields() -> dict:
    """Clear obsolete date filters whenever all dates is selected."""
    return {
        CONF_ALL_DATES: True,
        CONF_DATE_MODE: "any",
        CONF_DATE_START: None,
        CONF_DATE_END: None,
    }


def start_date_schema(values: dict | None = None) -> vol.Schema:
    values = values or {}
    marker = (vol.Required(CONF_DATE_START, default=values[CONF_DATE_START])
              if values.get(CONF_DATE_START) else vol.Required(CONF_DATE_START))
    return vol.Schema({marker: selector.DateSelector()})


def end_date_schema(values: dict | None = None) -> vol.Schema:
    values = values or {}
    marker = (vol.Optional(CONF_DATE_END, default=values[CONF_DATE_END])
              if values.get(CONF_DATE_END) else vol.Optional(CONF_DATE_END))
    return vol.Schema({marker: selector.DateSelector()})


def route_schema(values: dict | None, stations: list[str], targets=None) -> vol.Schema:
    """Show departure, destination and travel dates together."""
    values = values or {}
    fields = {}
    for key in (CONF_ORIGIN, CONF_DESTINATION):
        places = place_values(values.get(key))
        field = vol.Optional(key, default=places) if places else vol.Optional(key)
        # The chosen chips already show these stations.
        selected = {name.casefold() for name in places}
        choices = [name for name in stations if name.casefold() not in selected]
        fields[field] = _place_selector(choices)
        # The native number selector is a real drag slider in HA's config
        # flow. Keep it right below each place selection, not hidden in
        # Configure. There is deliberately no dynamic JS requirement.
        radius_key = f"{key}_radius_km"
        fields[vol.Required(
            radius_key, default=radius_default(values, key)
        )] = selector.NumberSelector(selector.NumberSelectorConfig(
            min=0, max=100, step=5, unit_of_measurement="km",
            mode=selector.NumberSelectorMode.SLIDER,
        ))
    fields[vol.Required(
        CONF_DIRECTION, default=values.get(CONF_DIRECTION, "forward")
    )] = select(["forward", "either"], "direction")
    # All-dates is the default. Date fields are not interactive on this
    # step; selecting a period guides the user through start and end dates.
    fields[vol.Required(
        CONF_ALL_DATES, default=all_dates_default(values)
    )] = selector.BooleanSelector()

    target = values.get(CONF_NOTIFY_TARGET, TARGET_OFF)
    enabled = values.get(CONF_NOTIFY_ENABLED, target != TARGET_OFF)
    fields[vol.Required(CONF_NOTIFY_ENABLED, default=bool(enabled))] = selector.BooleanSelector()
    if targets is None:
        targets = [(TARGET_OFF, "Off")]
    fields[vol.Required(CONF_NOTIFY_TARGET, default=target)] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[selector.SelectOptionDict(value=value, label=label) for value, label in targets],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )
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
        vol.Optional(CONF_MODEL_INCLUDE, default=values.get(CONF_MODEL_INCLUDE, "")):
            selector.TextSelector(),
        vol.Optional(CONF_MODEL_EXCLUDE, default=values.get(CONF_MODEL_EXCLUDE, "")):
            selector.TextSelector(),
        vol.Required(CONF_SORT_BY, default=values.get(CONF_SORT_BY, "date")):
            select(["date","short_drive","short_route","nearest_pickup","low_cost","best_margin"], "sort_by"),
    })


def updates_schema(values: dict | None = None) -> vol.Schema:
    values = values or {}
    return vol.Schema({
        vol.Required(CONF_SEARCH_ACTIVE, default=values.get(CONF_SEARCH_ACTIVE, True)):
            selector.BooleanSelector(),
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
        vol.Required(CONF_TOLL_IN_NOTIFICATIONS, default=values.get(CONF_TOLL_IN_NOTIFICATIONS, True)):
            selector.BooleanSelector(),
        vol.Required(CONF_ALERT_EXISTING, default=values.get(CONF_ALERT_EXISTING, False)):
            selector.BooleanSelector(),
        vol.Required(CONF_ALERT_UPDATES, default=values.get(CONF_ALERT_UPDATES, True)):
            selector.BooleanSelector(),
    })


def alerts_schema(values: dict | None = None) -> vol.Schema:
    """Separate alert rules, without changing selected phone or saved route."""
    values = values or {}
    return vol.Schema({
        vol.Optional(CONF_QUIET_START, default=values.get(CONF_QUIET_START, "")):
            selector.TextSelector(selector.TextSelectorConfig(
                type=selector.TextSelectorType.TEXT)),
        vol.Optional(CONF_QUIET_END, default=values.get(CONF_QUIET_END, "")):
            selector.TextSelector(selector.TextSelectorConfig(
                type=selector.TextSelectorType.TEXT)),
        vol.Required(CONF_QUIET_URGENT, default=values.get(CONF_QUIET_URGENT, False)):
            selector.BooleanSelector(),
        vol.Required(CONF_ONLY_FEASIBLE, default=values.get(CONF_ONLY_FEASIBLE, False)):
            selector.BooleanSelector(),
        vol.Required(CONF_MAX_TOLL, default=values.get(CONF_MAX_TOLL, 0)):
            selector.NumberSelector(selector.NumberSelectorConfig(
                min=0, max=10000, step=10, mode=selector.NumberSelectorMode.BOX)),
    })


def area_schema(values: dict, places: list[str]) -> vol.Schema:
    """Optional areas centered on a known provider station's GPS coordinate."""
    choices = sorted(set(places) | {
        name for key in ("origin_radius_name","destination_radius_name")
        if (name := values.get(key))
    })
    fields = {
        vol.Required(CONF_RADIUS_KM, default=values.get(CONF_RADIUS_KM, "0")):
            select(["0","25","50","100"], "radius_km"),
    }
    for key in ("origin_radius_name","destination_radius_name"):
        marker = vol.Optional(key,default=values[key]) if values.get(key) else vol.Optional(key)
        fields[marker] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=choices, mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
    return vol.Schema(fields)


def cost_schema(values: dict) -> vol.Schema:
    """No invented fuel price or usage: zero means estimate unavailable."""
    fields={}
    for key in (CONF_FUEL_USAGE,CONF_FUEL_PRICE,CONF_ELECTRIC_USAGE,CONF_ELECTRIC_PRICE):
        fields[vol.Required(key,default=values.get(key,0))] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=1000, step=0.1, mode=selector.NumberSelectorMode.BOX,
            )
        )
    return vol.Schema(fields)


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
    """Use saved stations, then learn from the latest publicly listed routes.

    Each Home Assistant installation keeps its own station history. Old
    locations remain selectable even after the corresponding car disappears.
    No extra API calls are needed for additional saved watch profiles.
    """
    active = [country for country in countries if country in ("NO", "SE")]
    catalog = await async_get_station_catalog(hass)
    results = await asyncio.gather(
        *(async_fetch_country(hass, country) for country in active),
        return_exceptions=True,
    )
    for country, result in zip(active, results):
        if isinstance(result, list):
            await catalog.async_learn(country, result)
    return catalog.suggestions(active)

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
            if not invalid and candidate.get(CONF_NOTIFY_ENABLED) and candidate.get(CONF_NOTIFY_TARGET) == TARGET_OFF:
                invalid = "notification_device_required"
            if not invalid and user_input.get(CONF_DATE_END) and not user_input.get(CONF_DATE_START):
                invalid = "missing_date"
            if not invalid:
                catalog = await async_get_station_catalog(self.hass)
                countries = candidate.get(CONF_COUNTRIES, ["NO"])
                points, invalid = validate_radius_settings(
                    candidate, catalog.located_stations(countries)
                )
                if not invalid:
                    candidate.update(points)
                    # Prevent old shared-radius settings from conflicting.
                    self._draft = candidate
                    if all_dates_default(candidate):
                        self._draft.update(all_dates_fields())
                        return self._finish()
                    return await self.async_step_registration_date_start()
            errors["base"] = invalid
        if self._stations is None:
            self._stations = await async_station_suggestions(
                self.hass, self._draft.get(CONF_COUNTRIES, ["NO"])
            )
        values = {**self._draft, **(user_input or {})}
        targets = notification_targets(self.hass, values.get(CONF_NOTIFY_TARGET))
        return self.async_show_form(
            step_id="route",
            data_schema=route_schema(values, self._stations, targets),
            errors=errors,
        )



    async def async_step_registration_date_start(self, user_input=None):
        """Choose a start date; next automatically opens the end-date form."""
        if user_input is not None:
            self._draft[CONF_DATE_START] = user_input[CONF_DATE_START]
            return await self.async_step_registration_date_end()
        return self.async_show_form(
            step_id="registration_date_start",
            data_schema=start_date_schema(self._draft),
        )

    async def async_step_registration_date_end(self, user_input=None):
        """Allow a single day or inclusive date range."""
        errors = {}
        if user_input is not None:
            values = {**self._draft, CONF_DATE_END: user_input.get(CONF_DATE_END)}
            candidate = {**values, CONF_ALL_DATES: False, **route_dates(values)}
            invalid = validation_error(candidate)
            if invalid is None:
                self._draft = candidate
                return self._finish()
            errors["base"] = invalid
        return self.async_show_form(
            step_id="registration_date_end",
            data_schema=end_date_schema({**self._draft, **(user_input or {})}),
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
            CONF_SEARCH_ACTIVE: True,
            CONF_ALL_DATES: True,
            CONF_SCAN_INTERVAL: DEFAULT_POLL_MINUTES,
            CONF_EVENTS: True,
            CONF_NOTIFY_TARGET: TARGET_OFF,
            CONF_NOTIFY_ENABLED: False,
            CONF_TOLL_IN_NOTIFICATIONS: True,
            CONF_MODEL_INCLUDE: "",
            CONF_MODEL_EXCLUDE: "",
            CONF_RADIUS_KM: "0",
            CONF_ALERT_EXISTING: False,
            CONF_ALERT_UPDATES: True,
            CONF_FUEL_USAGE: 0,
            CONF_FUEL_PRICE: 0,
            CONF_ELECTRIC_USAGE: 0,
            CONF_ELECTRIC_PRICE: 0,
            CONF_SORT_BY: "date",
            CONF_QUIET_START: "",
            CONF_QUIET_END: "",
            CONF_QUIET_URGENT: False,
            CONF_MAX_TOLL: 0,
            CONF_ONLY_FEASIBLE: False,
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
            step_id="init", menu_options=["route", "filters", "costs", "updates", "alerts"],
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
            if not invalid and user_input.get(CONF_NOTIFY_ENABLED) and user_input.get(CONF_NOTIFY_TARGET) == TARGET_OFF:
                invalid = "notification_device_required"
            if not invalid and user_input.get(CONF_DATE_END) and not user_input.get(CONF_DATE_START):
                invalid = "missing_date"
            if invalid is None:
                catalog=await async_get_station_catalog(self.hass)
                points, invalid = validate_radius_settings(
                    user_input,
                    catalog.located_stations(user_input[CONF_COUNTRIES]),
                )
                if invalid is None:
                    user_input.update(points)
                    if all_dates_default(user_input):
                        user_input.update(all_dates_fields())
                    else:
                        self._pending_route = user_input
                        return await self.async_step_edit_date_start()
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
        targets = notification_targets(self.hass, values.get(CONF_NOTIFY_TARGET))
        fields.update(route_schema(values, self._stations, targets).schema)
        return self.async_show_form(
            step_id="route", data_schema=vol.Schema(fields), errors=errors,
        )



    async def async_step_edit_date_start(self, user_input=None):
        """Continue directly to return-date selection after choosing from-date."""
        draft = getattr(self, "_pending_route", None)
        if draft is None:
            return await self.async_step_route()
        if user_input is not None:
            draft[CONF_DATE_START] = user_input[CONF_DATE_START]
            return await self.async_step_edit_date_end()
        return self.async_show_form(
            step_id="edit_date_start",
            data_schema=start_date_schema({**self._settings(), **draft}),
        )

    async def async_step_edit_date_end(self, user_input=None):
        """Save edited route, radius and date range atomically."""
        draft = getattr(self, "_pending_route", None)
        if draft is None:
            return await self.async_step_route()
        errors = {}
        if user_input is not None:
            values = {**draft, CONF_DATE_END: user_input.get(CONF_DATE_END)}
            candidate = {**values, CONF_ALL_DATES: False, **route_dates(values)}
            invalid = validation_error(candidate)
            if invalid is None:
                title = candidate.pop(CONF_WATCH_NAME, self.config_entry.title)
                if title != self.config_entry.title:
                    self.hass.config_entries.async_update_entry(
                        self.config_entry, title=title,
                    )
                self._pending_route = None
                return self.async_create_entry(
                    title="", data={**self.config_entry.options, **candidate},
                )
            errors["base"] = invalid
        return self.async_show_form(
            step_id="edit_date_end",
            data_schema=end_date_schema({**self._settings(), **draft, **(user_input or {})}),
            errors=errors,
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

    async def async_step_area(self, user_input=None):
        """Select center stations with valid coordinates; no external geocoder."""
        current=self._settings()
        countries=current.get(CONF_COUNTRIES,["NO"])
        catalog=await async_get_station_catalog(self.hass)
        located=catalog.located_stations(countries)
        if not located:
            # Fetch live coordinates the same way initial place suggestions do.
            await async_station_suggestions(self.hass,countries)
            located=catalog.located_stations(countries)
        errors={}
        if user_input is not None:
            radius=int(user_input.get(CONF_RADIUS_KM,"0"))
            opts={CONF_RADIUS_KM:str(radius)}
            for key in ("origin_radius_name","destination_radius_name"):
                name=user_input.get(key) or ""
                point=located.get(name) if name else None
                if radius and name and point is None:
                    errors["base"]="radius_station_unavailable"
                opts[key]=name
                opts[key.replace("_name","_point")]=point
            if radius and not (
                opts.get("origin_radius_name") or opts.get("destination_radius_name")
            ):
                errors["base"]="radius_center_required"
            if not errors:
                return self.async_create_entry(
                    title="",data={**self.config_entry.options,**opts},
                )
        values={**current,**(user_input or {})}
        return self.async_show_form(
            step_id="area",data_schema=area_schema(values,list(located)),errors=errors,
        )

    async def async_step_costs(self, user_input=None):
        """User-entered assumptions for partial running cost estimates."""
        if user_input is not None:
            return self.async_create_entry(
                title="",data={**self.config_entry.options,**user_input},
            )
        return self.async_show_form(
            step_id="costs",data_schema=cost_schema(self._settings()),
        )

    async def async_step_alerts(self, user_input=None):
        """Quiet hours and value filters; recipient remains in route settings."""
        if user_input is not None:
            start=(user_input.get(CONF_QUIET_START) or "").strip()
            end=(user_input.get(CONF_QUIET_END) or "").strip()
            from .trip_planner import quiet_now
            from datetime import datetime
            def valid(t):
                if not t:
                    return True
                try:
                    datetime.strptime(t,"%H:%M")
                    return True
                except ValueError:
                    return False
            if not valid(start) or not valid(end) or bool(start) != bool(end):
                return self.async_show_form(
                    step_id="alerts",
                    data_schema=alerts_schema({**self._settings(),**user_input}),
                    errors={"base": "invalid_quiet_hours"},
                )
            return self.async_create_entry(
                title="", data={**self.config_entry.options, **user_input,
                                CONF_QUIET_START:start, CONF_QUIET_END:end},
            )
        return self.async_show_form(
            step_id="alerts", data_schema=alerts_schema(self._settings()),
        )

    async def async_step_updates(self, user_input=None):
        """Configure update frequency and optional event broadcasts."""
        if user_input is not None:
            return self.async_create_entry(
                title="", data={**self.config_entry.options, **user_input},
            )
        return self.async_show_form(
            step_id="updates", data_schema=updates_schema(self._settings()),
        )
