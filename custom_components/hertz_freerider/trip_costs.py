"""Transparent partial travel-cost estimates. No invented fares or consumption."""

from __future__ import annotations

from math import isfinite


def positive(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)):
        return None
    value=float(value)
    return value if isfinite(value) and value>0 else None


def nonnegative(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)):
        return None
    value=float(value)
    return value if isfinite(value) and value>=0 else None


def cost_breakdown(ride, quote:dict | None, settings:dict) -> dict:
    """Known costs only. Fuel assumptions must be configured by the user.

    An estimate is *always partial*: ferries/fees and final provider billing
    may differ. Unknown amounts are never silently changed to zero.
    """
    toll=nonnegative(quote.get("amount_nok")) if isinstance(quote,dict) else None
    usage=price=energy=None
    unit=None
    if ride.fuel=="electric":
        usage=positive(settings.get("electric_kwh_100km"))
        price=positive(settings.get("electric_price_nok_kwh"))
        unit="kWh"
    elif ride.fuel in ("petrol","diesel"):
        usage=positive(settings.get("fuel_l_100km"))
        price=positive(settings.get("fuel_price_nok_l"))
        unit="L"
    distance=positive(ride.distance_km)
    if usage is not None and price is not None and distance is not None:
        energy=round(distance/100*usage*price,2)
    known=[v for v in (toll,energy) if v is not None]
    return {
        "toll_nok":toll,
        "energy_nok":energy,
        "energy_unit":unit if energy is not None else None,
        "known_subtotal_nok":round(sum(known),2) if known else None,
        "has_unknown_components":toll is None or energy is None or not isinstance(quote,dict) or quote.get("ferry_count") not in (0,),
        "estimate_only":True,
        "ferry_included":False,
        "note":"Delkostnad, ikke en garantert totalpris. Ferger, utleieravgifter og faktisk forbruk kan komme i tillegg.",
    }
