"""One Home Assistant device per Freerider watch, grouping its entities."""

from __future__ import annotations

from .const import DOMAIN


def watch_device_info(entry) -> dict:
    """Consistent device registry identity across all platforms."""
    return {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": entry.title,
        "manufacturer": "Freerider HA community",
        "model": "Freerider route monitor",
        "configuration_url": "https://github.com/Wesc-9/Freerider_HA",
    }
