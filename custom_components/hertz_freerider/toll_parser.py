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
    count = route.get("tollCount")
    ferry_count = route.get("ferryCount")
    return {
        "amount_nok": cost,
        "currency": "NOK",
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
