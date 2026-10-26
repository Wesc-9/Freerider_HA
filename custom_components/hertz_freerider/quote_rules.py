"""Provider-independent eligibility decisions for automatic toll estimates."""


def quote_eligibility(ride) -> str:
    """Only estimate ordinary Norwegian car routes from valid station metadata."""
    if (ride.pickup_country or "").lower() != "no" or (ride.return_country or "").lower() != "no":
        return "outside_norway"
    if ride.vehicle_type in ("van", "minibus"):
        return "unknown_heavy_vehicle_rate"
    coords = (
        ride.pickup_lat, ride.pickup_lon,
        ride.return_lat, ride.return_lon,
    )
    if any(value is None for value in coords):
        return "missing_coordinates"
    return "ok"
