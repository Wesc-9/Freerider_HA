"""Pure search pause policy, shared by the coordinator and switch.

An existing saved profile without an explicit search_active setting remains
enabled. The alerts switch is separate: disabling alerts alone does not
stop listings from being refreshed.
"""

from __future__ import annotations


def search_active(settings: dict) -> bool:
    return settings.get("search_active", True) is not False


def periodic_checks_enabled(settings: dict) -> bool:
    return search_active(settings) and settings.get("scan_mode", "automatic") == "automatic"
