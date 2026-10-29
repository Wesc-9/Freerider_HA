"""Pure, independent parser for Norway's documented road toll calculator.

The supplier is https://bompengeappen.no/api-docs. It returns route-specific
toll estimates derived from SVV/NVDB. No values are invented when unavailable.
"""

from __future__ import annotations

from math import isfinite


def _amount(value: object) -> float | None:
    """Return valid nonnegative monetary amounts including zero."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    amount = float(value)
    if not isfinite(amount) or amount < 0:
        return None
    return round(amount, 2)


def parse_toll_response(payload: object, *, electric: bool) -> dict:
    """Read first recommended route's billing, without AutoPASS discount.

    Hertz Norway states that ordinary toll tariffs are passed to customers
    without passing through the usual AutoPASS discount. This estimate never
    assumes a Hertz invoice will exactly equal a third-party calculation.
    """
    if not isinstance(payload, dict):
        raise ValueError("Invalid toll response: expected JSON object")
    billing = payload.get("_billing")
    if not isinstance(billing, dict):
        raise ValueError("Missing toll cost breakdown")
    routes = billing.get("routes")
    if not isinstance(routes, list) or not routes or not isinstance(routes[0], dict):
        raise ValueError("No recommended road route with toll billing")
    route = routes[0]
    rate = "tollSmallEvNoDiscount" if electric else "tollSmallNoDiscount"
    cost = _amount(route.get(rate))
    if cost is None:
        raise ValueError("No reliable no-discount toll rate available")

    stations = []
    for item in route.get("chargedStations") or []:
        if isinstance(item, dict) and item.get("name"):
            stations.append({
                "name": str(item["name"]),
                "covered_by_hour_rule": bool(item.get("_coveredByTimesregel", False)),
            })
    # Documented BompengeAppen _billing fields. Distance is in meters,
    # durationMin is minutes. The Hertz offer's own travel estimate is
    # preferred when available; these metrics are useful as a fallback.
    raw_distance = route.get("distance")
    raw_duration = route.get("durationMin")
    distance_km = (
        round(float(raw_distance) / 1000, 1)
        if _amount(raw_distance) is not None else None
    )
    duration_min = (
        round(float(raw_duration), 1)
        if _amount(raw_duration) is not None else None
    )
    # BompengeAppen forwards the road-planner's obstruction flag as
    # routes[i].isObstructed. This is a *route planning snapshot*, not a
    # real-time comprehensive DATEX traffic feed.
    route_payload = payload.get("routes")
    matched_route = None
    if isinstance(route_payload, list):
        expected_id = route.get("routeId")
        for suggestion in route_payload[:10]:
            if not isinstance(suggestion, dict):
                continue
            if expected_id is None or suggestion.get("routeId") == expected_id:
                matched_route = suggestion
                break
    flagged = matched_route.get("isObstructed") if matched_route else None
    # Never call a missing / null flag "clear roads".
    road_obstructed = flagged if isinstance(flagged, bool) else None
    raw_features = matched_route.get("obstructingFeatures") if matched_route else None
    obstruction_count = (
        min(len(raw_features), 100)
        if isinstance(raw_features, list) and road_obstructed is True else None
    )
    count = route.get("tollCount")
    ferry_count = route.get("ferryCount")
    return {
        "amount_nok": cost,
        "road_obstructed": road_obstructed,
        "road_obstruction_count": obstruction_count,
        "road_status_source": "SVV route planner via BompengeAppen" if road_obstructed is not None else None,
        "currency": "NOK",
        "distance_km": distance_km,
        "duration_min": duration_min,
        "vehicle_rate": "electric_no_discount" if electric else "small_vehicle_no_discount",
        "toll_count": count if isinstance(count, int) and not isinstance(count, bool) else None,
        "toll_stations": stations[:40],
        "ferry_count": ferry_count if isinstance(ferry_count, int) else None,
        "ferry_included": False,
        "refined": bool(billing.get("refined", False)),
        "source": str(billing.get("source") or "BompengeAppen"),
        "disclaimer": (
            "Estimate only for a proposed Norwegian road route, without "
            "AutoPASS discounts. Hertz may charge different amounts, VAT "
            "or fees. Ferry, fuel, charging and international fees excluded."
        ),
    }
