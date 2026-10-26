"""Availability count and inspectable listing details for each watch."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .device import watch_device_info
from .const import DOMAIN
from .offer_view import device_offers, offer_entity_name, offer_entity_state


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Expose match count and each current offer directly on the device page.

    Keep the original aggregate sensor for existing dashboards/automations.
    The separate live-offer entities are bounded, created as offers appear,
    and removed from the registry when the provider no longer lists them.
    """
    coordinator = hass.data[DOMAIN][entry.entry_id]
    live: dict[str, FreeriderLiveOffer] = {}
    uid_prefix = f"hertz_freerider_{entry.entry_id}_offer_"

    @callback
    def _sync_available_cars() -> None:
        # Failed requests must not erase listings or impersonate zero cars.
        if not coordinator.last_update_success:
            return
        desired = {ride.key: ride for ride in device_offers(coordinator.data)}
        registry = er.async_get(hass)
        desired_ids = {uid_prefix + ride.key for ride in desired.values()}

        # Remove stale entries left by a restart as well as running entities.
        # Do not touch the stable count sensor or a user's other entities.
        for registered in er.async_entries_for_config_entry(registry, entry.entry_id):
            if (registered.domain == "sensor"
                and registered.unique_id.startswith(uid_prefix)
                and registered.unique_id not in desired_ids):
                registry.async_remove(registered.entity_id)

        for key in tuple(live):
            if key not in desired:
                live.pop(key)
        added = []
        for key, ride in desired.items():
            if key not in live:
                sensor = FreeriderLiveOffer(coordinator, entry, ride)
                live[key] = sensor
                added.append(sensor)
        if added:
            async_add_entities(added)

    async_add_entities([
        FreeriderCount(coordinator, entry),
        FreeriderLastTollEstimate(coordinator, entry),
    ])
    _sync_available_cars()
    entry.async_on_unload(coordinator.async_add_listener(_sync_available_cars))


class FreeriderLiveOffer(CoordinatorEntity, SensorEntity):
    """A real currently matching offer, grouped under its saved-search device."""

    _attr_icon = "mdi:car"
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, ride) -> None:
        super().__init__(coordinator)
        self._ride_key = ride.key
        self._attr_unique_id = (
            f"hertz_freerider_{entry.entry_id}_offer_{ride.key}"
        )
        # Full provider model name is retained, destination distinguishes
        # two equal models heading to different return stations.
        self._attr_name = offer_entity_name(ride)
        self._attr_icon = (
            "mdi:truck-outline"
            if ride.vehicle_type in ("van", "minibus") else "mdi:car"
        )
        self._attr_device_info = watch_device_info(entry)

    def _current_offer(self):
        return next(
            (ride for ride in self.coordinator.data or ()
             if ride.key == self._ride_key),
            None,
        )

    @property
    def native_value(self):
        """Display the trip as the row state, rather than internal IDs."""
        offer = self._current_offer()
        return offer_entity_state(offer) if offer is not None else None

    @property
    def extra_state_attributes(self):
        """Readable details for tapping an individual offer on the device page."""
        offer = self._current_offer()
        if offer is None:
            return {"status": "no_longer_listed"}
        toll = self.coordinator.toll_estimates.get(offer.key)
        return {
            "bil": offer.vehicle,
            "fra": offer.origin,
            "til": offer.destination,
            "distanse_km": offer.distance_km,
            "kjoretid_min": offer.drive_minutes,
            "tilgjengelig_fra": offer.available_at,
            "tilbud_utloper": offer.offer_expires_at,
            "seneste_retur": offer.latest_return_at,
            "bom_estimat_nok": toll.get("amount_nok") if toll else None,
            "bom_merknad": (
                "Takstgruppe ukjent for større kjøretøy"
                if offer.vehicle_type in ("van", "minibus")
                else "Kun estimat; kan avvike fra faktisk kostnad"
            ),
            "lenke_til_freerider": offer.booking_url,
            "tilbud_id": offer.key,
        }


class FreeriderCount(CoordinatorEntity, SensorEntity):
    """Matched real offers; source failures are 'unavailable', not zero."""

    _attr_icon = "mdi:car-multiple"
    _attr_native_unit_of_measurement = "rides"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_device_info = watch_device_info(entry)
        self._attr_name = f"{entry.title} matching rides"
        self._attr_unique_id = f"hertz_freerider_{entry.entry_id}_count"

    @property
    def native_value(self):
        """Count matches only following a successful live data fetch."""
        return len(self.coordinator.data or [])

    @property
    def extra_state_attributes(self):
        """Expose a small list of actionable matches without bloating state."""
        return {
            "search_name": self.coordinator.entry.title,
            "filters": self.coordinator.settings,
            "source_errors": self.coordinator.last_source_errors,
            "rides": [
                {
                    **ride.as_event(),
                    "toll_estimate": self.coordinator.toll_estimates.get(ride.key),
                    "toll_estimate_status": (
                        "unknown_vehicle_weight_class"
                        if ride.vehicle_type in ("van", "minibus")
                        else "not_calculated"
                    ) if ride.key not in self.coordinator.toll_estimates else "calculated",
                }
                for ride in (self.coordinator.data or [])[:20]
            ],
            "total_matches": len(self.coordinator.data or []),
            "notification_target": self.coordinator.settings.get("notify_target", "off"),
            "notification_enabled": self.coordinator.settings.get("notify_enabled", True),
            "pending_notifications": len(self.coordinator.pending_notification_ids),
            "extra_costs": "Tolls may be payable. Fuel/charging may incur additional costs.",
            "tolls": "Norway: automatic estimates for eligible new cars (quota-limited); manual lookup via button. Van/minibus needs verified weight class.",
        }


class FreeriderLastTollEstimate(CoordinatorEntity, SensorEntity):
    """Latest manual or automatic Norwegian quote; unavailable is not zero."""

    _attr_icon = "mdi:cash"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = "NOK"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_device_info = watch_device_info(entry)
        self._attr_name = f"{entry.title} last toll estimate"
        self._attr_unique_id = f"hertz_freerider_{entry.entry_id}_toll_nok"

    @property
    def native_value(self):
        """Last successfully computed toll amount, manual or automatic."""
        quote = self.coordinator.last_toll_estimate
        return quote.get("amount_nok") if quote else None

    @property
    def extra_state_attributes(self):
        """Make charging assumptions and station details visible in HA."""
        return self.coordinator.last_toll_estimate or {
            "status": "not_calculated",
            "info": "Computed for eligible Norwegian passenger-car routes on new alerts; manual estimate button also available. Unknown is not free.",
            "fuel_charging_note": "Fuel/charging costs may apply.",
        }
