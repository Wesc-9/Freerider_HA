"""Validate radius choices from verified provider station coordinates.

Only real coordinate-bearing stations can be used as radius centers. The
same rules apply during first-time registration and when editing a watch.
"""
from __future__ import annotations

from .search_enhancements import distance_km


RADIUS_CHOICES = frozenset({"0", "25", "50", "100"})


def parse_radius_selection(values: dict, located: dict[str, dict]) -> tuple[dict, str | None]:
    """Return saved radius fields and a translated error key if invalid."""
    radius = str(values.get("radius_km", "0"))
    if radius not in RADIUS_CHOICES:
        return {}, "radius_invalid"

    result = {"radius_km": radius}
    if radius == "0":
        # Explicitly reset old center coordinates when turning radius off.
        for side in ("origin", "destination"):
            result[f"{side}_radius_name"] = ""
            result[f"{side}_radius_point"] = None
        return result, None

    for side in ("origin", "destination"):
        name = values.get(f"{side}_radius_name") or ""
        point = located.get(name) if name else None
        if name and (not isinstance(point, dict) or distance_km(
            point.get("lat"), point.get("lon"),
            point.get("lat"), point.get("lon"),
        ) is None):
            return {}, "radius_station_unavailable"
        result[f"{side}_radius_name"] = name
        result[f"{side}_radius_point"] = dict(point) if point else None

    if not (result["origin_radius_point"] or result["destination_radius_point"]):
        return {}, "radius_center_required"
    return result, None
