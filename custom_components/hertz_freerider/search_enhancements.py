"""Pure matching and event helpers for Freerider HA; no HA dependencies."""

from __future__ import annotations

from math import asin, cos, isfinite, radians, sin, sqrt


def _number(value, *, low=None, high=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    if not isfinite(result) or (low is not None and result < low) or (high is not None and result > high):
        return None
    return result


def distance_km(lat1, lon1, lat2, lon2) -> float | None:
    """Haversine surface distance; coordinates must come from official station data."""
    a = [_number(lat1,low=-90,high=90), _number(lon1,low=-180,high=180),
         _number(lat2,low=-90,high=90), _number(lon2,low=-180,high=180)]
    if any(v is None for v in a):
        return None
    la1,lo1,la2,lo2 = map(radians,a)
    h=sin((la2-la1)/2)**2+cos(la1)*cos(la2)*sin((lo2-lo1)/2)**2
    return round(12742*asin(min(1,sqrt(max(0,h)))),3)


def station_in_radius(point: dict | None, lat, lon, radius) -> bool:
    if not isinstance(point,dict):
        return False
    measured=distance_km(point.get("lat"),point.get("lon"),lat,lon)
    return measured is not None and measured <= radius


def model_terms(value: object) -> list[str]:
    """Semi-colon/newline-separated model names (not comma inside model titles)."""
    if not isinstance(value,str):
        return []
    return [t.strip().casefold() for t in value.replace("\n",";").split(";") if t.strip()]


def matches_model(model: str, include: object, exclude: object) -> bool:
    from unicodedata import normalize
    def fold(s):
        return "".join(c for c in normalize("NFKD",s.casefold()) if not __import__("unicodedata").combining(c))
    name=fold(model)
    allowed=[fold(t) for t in model_terms(include)]
    blocked=[fold(t) for t in model_terms(exclude)]
    return (not allowed or any(x in name for x in allowed)) and not any(x in name for x in blocked)


SIGNATURE_FIELDS = ("vehicle","origin","destination","available_at","offer_expires_at","latest_return_at")
DATE_FIELDS = ("available_at","offer_expires_at","latest_return_at")


def offer_snapshot(ride) -> dict:
    return {k:getattr(ride,k,None) for k in SIGNATURE_FIELDS}


def classify_offers(
    previous: dict[str,dict] | None,
    current: list,
    successful_countries: set[str],
    seen_ids: set[str] | None,
    notify_existing: bool = False,
) -> tuple[list[tuple[object,str]], list[dict], dict[str,dict]]:
    """Snapshot delta; never mark rides removed when their country feed failed.

    Return alerts (ride, kind), bounded history entries (without timestamp)
    and next snapshot. First run is baseline unless explicitly opted in.
    """
    before=previous or {}
    baseline=previous is None
    current_by_id={ride.key:ride for ride in current}
    next_state={key:value for key,value in before.items()
                if key.split(":",1)[0] not in successful_countries}
    alerts=[]
    events=[]
    for ride in current:
        snapshot=offer_snapshot(ride)
        next_state[ride.key]=snapshot
        prior=before.get(ride.key)
        if baseline:
            if notify_existing or (seen_ids is not None and ride.key not in seen_ids):
                alerts.append((ride,"existing" if notify_existing and seen_ids is None else "new"))
            if seen_ids is None:
                continue
        if prior is None:
            if not baseline:
                alerts.append((ride,"new"))
            events.append({"id":ride.key,"kind":"new","route":f"{ride.origin} → {ride.destination}"})
        elif any(prior.get(k)!=snapshot[k] for k in DATE_FIELDS):
            alerts.append((ride,"updated"))
            events.append({"id":ride.key,"kind":"updated","route":f"{ride.origin} → {ride.destination}"})
    if not baseline:
        for key, snapshot in before.items():
            if key.split(":",1)[0] in successful_countries and key not in current_by_id:
                events.append({"id":key,"kind":"removed","route":f'{snapshot.get("origin","")} → {snapshot.get("destination","")}'})
    return alerts, events, next_state
