"""Poll source adapters, maintain search results and emit new-offer events."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from time import monotonic
import logging

from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_COUNTRIES, CONF_EVENTS, CONF_SCAN_INTERVAL, CONF_SCAN_MODE,
    DEFAULT_POLL_MINUTES, DOMAIN, EVENT_NEW_RIDE, CONF_NOTIFY_TARGET, CONF_NOTIFY_ENABLED,
    CONF_TOLL_IN_NOTIFICATIONS, CONF_ALERT_EXISTING, CONF_ALERT_UPDATES,
    CONF_SORT_BY, CONF_QUIET_START, CONF_QUIET_END, CONF_QUIET_URGENT,
    CONF_MAX_TOLL, CONF_ONLY_FEASIBLE,
)
from .filters import Ride, filter_rides
from .source import async_fetch_country
from .notifications import (
    TARGET_OFF, async_send_notification, notification_content, test_notification_content,
)
from .station_catalog import async_get_station_catalog
from .tolls import async_estimate_toll, TollLookupError
from .quote_cache import async_get_quote_catalog
from .quote_rules import quote_eligibility
from .search_enhancements import classify_offers
from .trip_costs import cost_breakdown
from .trip_planner import sort_offers, journey_feasibility, quiet_now, is_urgent
from zoneinfo import ZoneInfo

_LOGGER = logging.getLogger(__name__)
MAX_REMEMBERED = 1500


class FreeriderCoordinator(DataUpdateCoordinator[list[Ride]]):
    """One independent saved route, editable through integration options."""

    def __init__(self, hass, entry) -> None:
        self.entry = entry
        self.settings = {**entry.data, **entry.options}
        self.seen_store = Store(hass, 1, f"{DOMAIN}_seen_{entry.entry_id}")
        self.seen_ids: list[str] | None = None
        self.pending_notification_ids: list[str] = []
        self.favorite_offers: dict[str, dict] = {}
        self._force_source_fetch = False
        self.offer_snapshots: dict[str,dict] | None = None
        self.offer_history: list[dict] = []
        self.last_success_utc: str | None = None
        self.last_attempt_utc: str | None = None
        self.last_alert_utc: str | None = None
        self.sent_alert_count = 0
        self.last_alert_error: str | None = None
        self.last_source_errors: dict[str, str] = {}
        self.toll_estimates: dict[str, dict] = {}
        self._toll_cache: dict[tuple[str, str], tuple[float, dict]] = {}
        self.last_toll_estimate: dict | None = None
        automatic = self.settings.get(CONF_SCAN_MODE, "automatic") == "automatic"
        interval = max(15, min(120, int(self.settings.get(
            CONF_SCAN_INTERVAL, DEFAULT_POLL_MINUTES
        ))))
        super().__init__(
            hass,
            _LOGGER,
            name=f"Freerider {entry.title}",
            update_interval=timedelta(minutes=interval) if automatic else None,
        )

    async def async_initialize(self) -> None:
        """Load recent ID history before performing the first refresh."""
        loaded = await self.seen_store.async_load()
        if isinstance(loaded, dict) and isinstance(loaded.get("ids"), list):
            self.seen_ids = [str(key) for key in loaded["ids"]][-MAX_REMEMBERED:]
            previous_pending = loaded.get("pending", [])
            if isinstance(previous_pending, list):
                self.pending_notification_ids = [
                    key for key in previous_pending if isinstance(key, str)
                ][-80:]
            snapshots=loaded.get("snapshots")
            if isinstance(snapshots,dict):
                self.offer_snapshots={
                    key:val for key,val in snapshots.items()
                    if isinstance(key,str) and isinstance(val,dict)
                }
            history=loaded.get("history")
            if isinstance(history,list):
                self.offer_history=[ev for ev in history if isinstance(ev,dict)][-100:]
            self.last_success_utc=loaded.get("last_success_utc")
            self.last_alert_utc=loaded.get("last_alert_utc")
            self.sent_alert_count=int(loaded.get("sent_alert_count") or 0)
            fav=loaded.get("favorite_offers")
            if isinstance(fav,dict):
                self.favorite_offers={key:value for key,value in list(fav.items())[:80]
                                      if isinstance(key,str) and isinstance(value,dict)}


    async def _async_update_data(self) -> list[Ride]:
        self.last_attempt_utc = datetime.now(timezone.utc).isoformat()
        countries = self.settings.get(CONF_COUNTRIES, ["NO"])
        force=self._force_source_fetch
        self._force_source_fetch=False
        results = await asyncio.gather(
            *(async_fetch_country(self.hass, country, force=force) for country in countries),
            return_exceptions=True,
        )
        valid: list[Ride] = []
        succeeded = False
        self.last_source_errors = {}
        for country, result in zip(countries, results):
            if isinstance(result, BaseException):
                self.last_source_errors[country] = str(result)
            elif isinstance(result, list):
                succeeded = True
                valid.extend(result)
            else:
                self.last_source_errors[country] = "Unexpected adapter response"

        # Failed providers must never be reported as zero available cars.
        if not succeeded:
            raise UpdateFailed("; ".join(
                f"{c}: {err}" for c, err in self.last_source_errors.items()
            ) or "No active Freerider source")

        # Learn stations from ALL successfully fetched routes, not only those
        # matching this particular saved search. The catalog survives restarts
        # and is shared between every Freerider profile in this HA instance.
        catalog = await async_get_station_catalog(self.hass)
        for country, result in zip(countries, results):
            if isinstance(result, list):
                await catalog.async_learn(country, result)

        # One offer can be exposed by several provider views: de-duplicate IDs.
        unique = {ride.key: ride for ride in valid}
        # A partial provider outage must not make previously reported cars
        # disappear from sensors. Retain their last cached offers, but mark
        # the overall search status as partial/stale.
        failed_countries=set(self.last_source_errors)
        for ride in self.data or []:
            if ride.source_country in failed_countries:
                unique.setdefault(ride.key,ride)
        matched = filter_rides(list(unique.values()), self.settings)
        cost_by_id = {
            ride.key: cost_breakdown(ride,self.toll_estimates.get(ride.key),self.settings)
            for ride in matched
        }
        home = None
        if self.settings.get(CONF_SORT_BY) == "nearest_pickup":
            lat,lon=self.hass.config.latitude,self.hass.config.longitude
            if lat is not None and lon is not None:
                home=(float(lat),float(lon))
        matched=sort_offers(
            matched,self.settings.get(CONF_SORT_BY,"date"),cost_by_id,home=home,
        )
        await self._remember_and_notify(
            matched,
            {country for country, result in zip(countries, results)
             if isinstance(result, list)},
        )
        return matched

    async def _remember_and_notify(
        self, matched: list[Ride], successful_countries: set[str]
    ) -> None:
        """Record offer history and send new/changed notifications at most once.

        Avoid false 'removed' events for a failed country's source. Persistent
        snapshots and failed-delivery queue survive Home Assistant restarts.
        """
        previous=set(self.seen_ids) if self.seen_ids is not None else None
        old_pending=list(self.pending_notification_ids)
        before=self.offer_snapshots
        alerts, changes, latest=classify_offers(
            before, matched, successful_countries, previous,
            notify_existing=bool(self.settings.get(CONF_ALERT_EXISTING,False)),
        )
        self.offer_snapshots=latest
        now=datetime.now(timezone.utc).isoformat()
        self.last_success_utc=now
        if changes:
            self.offer_history=(self.offer_history+[
                {**change,"observed_at":now} for change in changes
            ])[-100:]

        # Preserve existing event contract for new cars; emit a separate
        # event for changed offer dates instead of mislabelling it as new.
        if self.settings.get(CONF_EVENTS,True):
            for ride,kind in alerts:
                if kind=="updated" and not self.settings.get(CONF_ALERT_UPDATES,True):
                    continue
                self.hass.bus.async_fire(
                    EVENT_NEW_RIDE if kind in ("new","existing") else f"{DOMAIN}_offer_updated",
                    {"entry_id":self.entry.entry_id,"watch_name":self.entry.title,
                     "change":kind,**ride.as_event()},
                )

        target=self.settings.get(CONF_NOTIFY_TARGET,TARGET_OFF)
        wall_time=datetime.now(ZoneInfo("Europe/Oslo")).replace(tzinfo=None)
        quiet=quiet_now(self.settings.get(CONF_QUIET_START),
                        self.settings.get(CONF_QUIET_END),wall_time)
        enabled=target != TARGET_OFF and self.settings.get(CONF_NOTIFY_ENABLED,True)
        queued={ride.key:kind for ride,kind in alerts if
                kind!="updated" or self.settings.get(CONF_ALERT_UPDATES,True)}
        if enabled:
            for key in self.pending_notification_ids:
                queued.setdefault(key,"retry")
            still_pending=[]
            attempts=0
            remaining_toll_calls=2
            quote_catalog=None
            for ride in matched:
                if ride.key not in queued:
                    continue
                if ride.source_country not in successful_countries:
                    # Never notify from a stale cached feed after source outage.
                    still_pending.append(ride.key)
                    continue
                if quiet and not (
                    self.settings.get(CONF_QUIET_URGENT,False)
                    and is_urgent(ride,wall_time)
                ):
                    still_pending.append(ride.key)
                    continue
                if self.settings.get(CONF_ONLY_FEASIBLE,False):
                    feasibility=journey_feasibility(ride,wall_time)
                    if feasibility["status"] in ("insufficient","expired"):
                        continue
                if attempts>=8:
                    still_pending.append(ride.key)
                    continue
                attempts+=1
                quote=self.toll_estimates.get(ride.key)
                toll_status="cached" if quote is not None else "not_calculated"
                if quote is None and self.settings.get(CONF_TOLL_IN_NOTIFICATIONS,True):
                    reason=quote_eligibility(ride)
                    if reason!="ok":
                        toll_status=reason
                    elif remaining_toll_calls<=0:
                        toll_status="scan_limit"
                    else:
                        remaining_toll_calls-=1
                        try:
                            if quote_catalog is None:
                                quote_catalog=await async_get_quote_catalog(self.hass)
                            quote,toll_status=await quote_catalog.async_quote(ride)
                            if quote is not None:
                                self.toll_estimates[ride.key]=quote
                                self.last_toll_estimate=quote
                        except Exception:
                            toll_status="provider_error"
                            _LOGGER.exception("Freerider toll enrichment failed for %s",ride.key)
                cost=cost_breakdown(ride,quote,self.settings)
                maximum=float(self.settings.get(CONF_MAX_TOLL,0) or 0)
                if maximum > 0:
                    if quote is None or quote.get("amount_nok") is None:
                        still_pending.append(ride.key)
                        continue
                    if float(quote["amount_nok"]) > maximum:
                        continue
                try:
                    delivered=await async_send_notification(
                        self.hass,target,notification_content(
                            ride,self.entry.title,self.hass.config.language,
                            toll_estimate=quote,toll_status=toll_status,
                            cost_estimate=cost,
                            alert_kind=queued[ride.key],
                        ),
                    )
                except Exception as exc:
                    _LOGGER.warning("Freerider push failed for %s: %s",ride.key,exc)
                    self.last_alert_error=str(exc)[:200]
                    delivered=False
                if delivered:
                    self.sent_alert_count+=1
                    self.last_alert_utc=now
                    self.last_alert_error=None
                else:
                    still_pending.append(ride.key)
            self.pending_notification_ids=still_pending[-80:]
        else:
            self.pending_notification_ids=[]

        merged=list(dict.fromkeys([
            *(self.seen_ids or []),*(ride.key for ride in matched),
        ]))[-MAX_REMEMBERED:]
        self.seen_ids=merged
        # Save after every successful fetch to persist history and diagnostics,
        # even if no new offer happens on this scan.
        await self._save_watch_state()

    async def _save_watch_state(self) -> None:
        """Persist monitoring and saved favorites without external services."""
        await self.seen_store.async_save({
            "ids":self.seen_ids or [],
            "pending":self.pending_notification_ids,
            "snapshots":self.offer_snapshots,
            "history":self.offer_history,
            "last_success_utc":self.last_success_utc,
            "last_alert_utc":self.last_alert_utc,
            "sent_alert_count":self.sent_alert_count,
            "favorite_offers":self.favorite_offers,
        })

    async def async_set_favorite(self, ride_id: str, favorite: bool) -> None:
        """Store an offer bookmark locally; no vehicle is reserved."""
        if favorite:
            ride=next((r for r in self.data or [] if r.key==ride_id),None)
            if ride is None:
                raise ValueError("Selected offer is no longer available")
            self.favorite_offers[ride_id]={
                **ride.as_event(),
                "saved_at":datetime.now(timezone.utc).isoformat(),
            }
            self.favorite_offers=dict(list(self.favorite_offers.items())[-80:])
        else:
            self.favorite_offers.pop(ride_id,None)
        await self._save_watch_state()
        self.async_set_updated_data(list(self.data or []))

    async def async_force_refresh(self) -> None:
        """Manual refresh bypasses the feed age, but not 60s cooldown."""
        self._force_source_fetch=True
        await self.async_request_refresh()

    async def async_send_test_notification(self) -> bool:
        """User-triggered validation of the selected mobile destination."""
        target = self.settings.get(CONF_NOTIFY_TARGET, TARGET_OFF)
        if not target or target == TARGET_OFF:
            return False
        language = self.hass.config.language
        if self.data:
            # Preview an actual currently matched route (no new offer event
            # and no additional toll API call just for a test).
            ride = self.data[0]
            payload = notification_content(
                ride,
                self.entry.title,
                language,
                toll_estimate=self.toll_estimates.get(ride.key),
            )
            norwegian = language.lower().startswith(("nb", "nn", "no"))
            payload["title"] = (
                "🧪 Freerider HA · Testvarsel"
                if norwegian else "🧪 Freerider HA · Test notification"
            )
            payload["message"] += (
                "\n🧪 Dette er kun en forhåndsvisning, ikke et nytt treff."
                if norwegian else
                "\n🧪 Preview only; this is not a new car alert."
            )
        else:
            payload = test_notification_content(self.entry.title, language)
        return await async_send_notification(self.hass, target, payload)

    async def async_calculate_toll(
        self, ride_id: str, start_time: str | None = None
    ) -> dict:
        """Run a manually requested toll lookup for an exact matching ride."""
        match = next((ride for ride in (self.data or []) if ride.key == ride_id), None)
        if match is None:
            raise TollLookupError("Ride ID is not in the current matching results")
        key = (ride_id, start_time or "")
        stored = self._toll_cache.get(key)
        if stored and monotonic() - stored[0] < 3600:
            estimate = dict(stored[1])
        else:
            estimate = await async_estimate_toll(self.hass, match, start_time)
            self._toll_cache[key] = (monotonic(), dict(estimate))
            # Limit in-memory cache size (quotas belong to external provider).
            if len(self._toll_cache) > 100:
                self._toll_cache.pop(next(iter(self._toll_cache)))

        self.toll_estimates[ride_id] = estimate
        self.last_toll_estimate = estimate
        # Notify Home Assistant sensors; do not emit a new-car event for a toll
        # calculation, which would otherwise trigger spurious push notifications.
        self.async_set_updated_data(list(self.data or []))
        return estimate
