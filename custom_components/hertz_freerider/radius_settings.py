"""Pure GPS-backed radius settings shared by registration and edit flow.

The two sliders operate independently: 0 km keeps the original exact/alias
matching; a positive radius adds provider-confirmed stations near each
selected reference point. Never guess coordinates for custom text stations.
"""
from __future__ import annotations

if __package__:
    from .filters import normalized, place_values
    from .search_enhancements import distance_km
else:
    from filters import normalized, place_values
    from search_enhancements import distance_km

RADIUS_STEP_KM = 5
MAX_RADIUS_KM = 100
SIDES = ("origin", "destination")


def radius_default(values: dict, side: str) -> int:
    """Show existing legacy radius on first edit, then use new explicit value."""
    key = f"{side}_radius_km"
    if key in values:
        return values[key] if values[key] is not None else 0
    if values.get(f"{side}_radius_name"):
        try:
            return int(values.get("radius_km", 0) or 0)
        except (TypeError, ValueError):
            return 0
    return 0


def validate_radius_settings(values: dict, located: dict[str, dict]) -> tuple[dict, str | None]:
    """Validate both sliders and resolve every selected center from real GPS.

    No provider GPS for a selected origin/destination => a clear form error
    rather than silently omitting that radius center.
    """
    known = {normalized(name): point for name, point in located.items()}
    updates: dict = {"radius_km": "0"}  # turn off previous legacy shared radius
    for side in SIDES:
        field = f"{side}_radius_km"
        raw = values.get(field, radius_default(values, side))
        if isinstance(raw, bool):
            return {}, "radius_invalid"
        try:
            radius = int(raw)
            if float(raw) != radius:
                return {}, "radius_invalid"
        except (ValueError, TypeError):
            return {}, "radius_invalid"
        if radius < 0 or radius > MAX_RADIUS_KM or radius % RADIUS_STEP_KM:
            return {}, "radius_invalid"

        points = []
        selected = place_values(values.get(side))
        if radius and not selected:
            return {}, "radius_center_required"
        if radius:
            for name in selected:
                point = known.get(normalized(name))
                if (not isinstance(point, dict)
                    or distance_km(point.get("lat"), point.get("lon"),
                                   point.get("lat"), point.get("lon")) is None):
                    return {}, "radius_station_unavailable"
                coords = {"lat": float(point["lat"]), "lon": float(point["lon"])}
                if coords not in points:
                    points.append(coords)
        updates[field] = radius
        updates[f"{side}_radius_points"] = points
    # Do not keep any stale previous center when changing registration settings.
    return updates, None
