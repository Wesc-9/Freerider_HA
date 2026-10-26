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
