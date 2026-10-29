"""Compatibility helpers for legacy searches and newer trip subentries.

A trip has its own coordinator, cache and device identity while Home Assistant
still owns the actual config entry. Never store a per-trip API credential.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .const import DOMAIN

SUBENTRY_TYPE = "trip"
LEGACY_WATCH_FIELD = "countries"


@dataclass
class TripProfile:
    """Runtime view of a trip, backed by a parent config subentry."""

    entry_id: str
    title: str
    data: dict[str, Any]
    options: dict[str, Any]
    parent_entry_id: str
    subentry_id: str


def has_legacy_watch(entry) -> bool:
    """Preserve existing configuration entries and entity IDs."""
    return LEGACY_WATCH_FIELD in entry.data


def trip_profiles(entry) -> list[TripProfile]:
    """Each saved trip is an independent watch sharing the parent's API key."""
    return [
        TripProfile(
            entry_id=f"{entry.entry_id}_{subentry.subentry_id}",
            title=subentry.title,
            data=dict(subentry.data),
            options={},
            parent_entry_id=entry.entry_id,
            subentry_id=subentry.subentry_id,
        )
        for subentry in entry.get_subentries_of_type(SUBENTRY_TYPE)
    ]


def all_watch_profiles(entry) -> list:
    """Include old searches without resetting their devices or notifications."""
    return ([entry] if has_legacy_watch(entry) else []) + trip_profiles(entry)


def update_watch_setting(hass, profile, key: str, value: Any) -> None:
    """Change only the intended trip, never unrelated trips or global API data."""
    if isinstance(profile, TripProfile):
        parent = hass.config_entries.async_get_entry(profile.parent_entry_id)
        if parent is None:
            raise ValueError("Freerider parent configuration was removed")
        subentry = parent.subentries.get(profile.subentry_id)
        if subentry is None:
            raise ValueError("Freerider trip was removed")
        hass.config_entries.async_update_subentry(
            parent, subentry, data={**subentry.data, key: value}
        )
    else:
        hass.config_entries.async_update_entry(
            profile, options={**profile.options, key: value}
        )
