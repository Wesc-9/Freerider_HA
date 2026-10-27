"""Shared configuration constants."""

DOMAIN = "hertz_freerider"
COUNTRIES = {"NO": "Norway", "SE": "Sweden", "DK": "Denmark (source not ready)"}
OFFICIAL_SITES = {
    "NO": "https://hertzfreerider.no/",
    "SE": "https://hertzfreerider.se/",
    "DK": "https://hertzfreerider.nu/",
}
CONF_WATCH_NAME = "watch_name"
CONF_COUNTRIES = "countries"
CONF_ORIGIN = "origin"
CONF_DESTINATION = "destination"
CONF_DIRECTION = "direction"
CONF_DATE_MODE = "date_mode"
CONF_DATE_START = "date_start"
CONF_DATE_END = "date_end"
CONF_TRANSMISSION = "transmission"
CONF_VEHICLE_TYPE = "vehicle_type"
CONF_FUEL = "fuel"
CONF_MIN_SEATS = "min_seats"
CONF_SCAN_MODE = "scan_mode"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_EVENTS = "notify_events"
CONF_NOTIFY_TARGET = "notify_target"
CONF_NOTIFY_ENABLED = "notify_enabled"
CONF_TOLL_IN_NOTIFICATIONS = "toll_in_notifications"
EVENT_NEW_RIDE = "hertz_freerider_new_ride"
SERVICE_REFRESH = "refresh"
DEFAULT_POLL_MINUTES = 30
MIN_POLL_MINUTES = 15
MAX_POLL_MINUTES = 120

# Advanced filters, meaningful alerts and user-supplied cost assumptions.
CONF_MODEL_INCLUDE = "model_include"
CONF_MODEL_EXCLUDE = "model_exclude"
CONF_RADIUS_KM = "radius_km"
CONF_ALERT_EXISTING = "alert_existing_first_scan"
CONF_ALERT_UPDATES = "alert_offer_changes"
CONF_FUEL_USAGE = "fuel_l_100km"
CONF_FUEL_PRICE = "fuel_price_nok_l"
CONF_ELECTRIC_USAGE = "electric_kwh_100km"
CONF_ELECTRIC_PRICE = "electric_price_nok_kwh"

CONF_SORT_BY = "sort_by"
CONF_QUIET_START = "quiet_start"
CONF_QUIET_END = "quiet_end"
CONF_QUIET_URGENT = "quiet_urgent_bypass"
CONF_MAX_TOLL = "max_toll_nok"
CONF_ONLY_FEASIBLE = "alerts_only_feasible"
CONF_SEARCH_ACTIVE = "search_active"

# Independent registration sliders, 0 = exact stations only.
CONF_ORIGIN_RADIUS_KM = "origin_radius_km"
CONF_DESTINATION_RADIUS_KM = "destination_radius_km"

CONF_ALL_DATES = "all_dates"
