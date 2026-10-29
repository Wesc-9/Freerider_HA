"""Native Home Assistant 'Add trip' subentries for Freerider HA.

One shared API credential is configured on the parent. Every trip has its own
route, dates, destination, notification target, history and device.
"""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import (
    CONF_COUNTRIES, CONF_DATE_START, CONF_DATE_END, CONF_DATE_MODE,
    CONF_ORIGIN, CONF_DESTINATION, CONF_WATCH_NAME, CONF_TOLL_API_KEY,
    CONF_NOTIFY_ENABLED, CONF_NOTIFY_TARGET, CONF_TRANSMISSION,
    CONF_DIRECTION, CONF_VEHICLE_TYPE, CONF_FUEL, CONF_MIN_SEATS,
    CONF_SCAN_MODE, CONF_SCAN_INTERVAL, CONF_EVENTS, CONF_SEARCH_ACTIVE,
    CONF_TOLL_IN_NOTIFICATIONS, CONF_MODEL_INCLUDE, CONF_MODEL_EXCLUDE,
    CONF_ALERT_EXISTING, CONF_ALERT_UPDATES, CONF_FUEL_USAGE, CONF_FUEL_PRICE,
    CONF_ELECTRIC_USAGE, CONF_ELECTRIC_PRICE, CONF_SORT_BY,
    CONF_QUIET_START, CONF_QUIET_END, CONF_QUIET_URGENT, CONF_MAX_TOLL,
    CONF_ONLY_FEASIBLE, DEFAULT_POLL_MINUTES,
)
from .notifications import TARGET_OFF, notification_targets
from .filters import place_values
from .radius_settings import validate_radius_settings
from .station_catalog import async_get_station_catalog


def _trip_defaults() -> dict:
    """Defaults match earlier saved searches; every trip can override them."""
    return {
        CONF_TRANSMISSION: "any",
        CONF_DIRECTION: "forward",
        CONF_VEHICLE_TYPE: "any",
        CONF_FUEL: "any",
        CONF_MIN_SEATS: 0,
        CONF_SCAN_MODE: "automatic",
        CONF_SEARCH_ACTIVE: True,
        CONF_SCAN_INTERVAL: DEFAULT_POLL_MINUTES,
        CONF_EVENTS: True,
        CONF_NOTIFY_TARGET: TARGET_OFF,
        CONF_NOTIFY_ENABLED: False,
        CONF_TOLL_IN_NOTIFICATIONS: True,
        CONF_MODEL_INCLUDE: "",
        CONF_MODEL_EXCLUDE: "",
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


async def _validated_trip(hass, values: dict) -> tuple[dict, str | None]:
    """Validate route and date selectors, use the same rules as legacy search."""
    from .config_flow import submitted_dates, validation_error

    dates, error = submitted_dates(values)
    candidate = {
        **values,
        CONF_COUNTRIES: [c.upper() for c in values.get(CONF_COUNTRIES, [])],
        CONF_ORIGIN: place_values(values.get(CONF_ORIGIN)),
        CONF_DESTINATION: place_values(values.get(CONF_DESTINATION)),
        **dates,
    }
    name = (candidate.get(CONF_WATCH_NAME) or "").strip()
    if not name or len(name) > 80:
        return candidate, "invalid_name"
    candidate[CONF_WATCH_NAME] = name
    if not error:
        error = validation_error(candidate)
    if (not error and candidate.get(CONF_NOTIFY_ENABLED)
            and candidate.get(CONF_NOTIFY_TARGET) == TARGET_OFF):
        error = "notification_device_required"
    if not error:
        catalog = await async_get_station_catalog(hass)
        point_settings, error = validate_radius_settings(
            candidate, catalog.located_stations(candidate.get(CONF_COUNTRIES, ["NO"])),
        )
        if not error:
            candidate.update(point_settings)
    candidate.pop(CONF_TOLL_API_KEY, None)
    return candidate, error


class FreeriderTripSubentryFlow(config_entries.ConfigSubentryFlow):
    """A subentry is one live Freerider route, not a decorative placeholder."""

    def __init__(self) -> None:
        self._draft: dict = {}
        self._stations: list[str] | None = None

    async def async_step_user(self, user_input=None):
        """Pick a search name and countries without repeating the API key."""
        from .config_flow import countries_schema, validation_error
        errors = {}
        if user_input is not None:
            candidate = dict(user_input)
            candidate[CONF_COUNTRIES] = [
                country.upper() for country in user_input.get(CONF_COUNTRIES, [])
            ]
            name = (candidate.get(CONF_WATCH_NAME) or "").strip()
            invalid = (
                "invalid_name" if not name or len(name) > 80
                else validation_error(candidate)
            )
            if invalid is None:
                candidate[CONF_WATCH_NAME] = name
                self._draft = candidate
                return await self.async_step_route()
            errors["base"] = invalid
        return self.async_show_form(
            step_id="user",
            data_schema=countries_schema(user_input, include_api_key=False),
            errors=errors,
        )

    async def async_step_route(self, user_input=None):
        """Add places, radii and dates; then create the actual trip."""
        from .config_flow import route_schema, async_station_suggestions
        errors = {}
        if user_input is not None:
            candidate, error = await _validated_trip(
                self.hass, {**self._draft, **user_input}
            )
            if error is None:
                title = candidate.pop(CONF_WATCH_NAME)
                return self.async_create_entry(
                    title=title,
                    data={**_trip_defaults(), **candidate},
                )
            errors["base"] = error
        if self._stations is None:
            self._stations = await async_station_suggestions(
                self.hass, self._draft.get(CONF_COUNTRIES, ["NO"])
            )
        values = {**self._draft, **(user_input or {})}
        return self.async_show_form(
            step_id="route",
            data_schema=route_schema(
                values, self._stations,
                notification_targets(self.hass, values.get(CONF_NOTIFY_TARGET))
            ),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input=None):
        """Edit only this trip; preserve the parent API and other trips."""
        from .config_flow import (
            countries_schema, route_schema, async_station_suggestions
        )
        parent = self._get_entry()
        subentry = self._get_reconfigure_subentry()
        current = dict(subentry.data)
        errors = {}
        if user_input is not None:
            candidate, error = await _validated_trip(
                self.hass, {
                    **current, **user_input,
                    CONF_WATCH_NAME: user_input.get(
                        CONF_WATCH_NAME, subentry.title,
                    ),
                }
            )
            if error is None:
                title = candidate.pop(CONF_WATCH_NAME)
                return self.async_update_and_abort(
                    parent, subentry, title=title, data=candidate
                )
            errors["base"] = error

        countries = current.get(CONF_COUNTRIES, ["NO"])
        stations = await async_station_suggestions(self.hass, countries)
        values = {**current, **(user_input or {}), CONF_WATCH_NAME: (
            user_input or {}
        ).get(CONF_WATCH_NAME, subentry.title)}
        fields = dict(countries_schema(values, include_api_key=False).schema)
        fields.update(route_schema(
            values, stations,
            notification_targets(self.hass, values.get(CONF_NOTIFY_TARGET))
        ).schema)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(fields),
            errors=errors,
        )
