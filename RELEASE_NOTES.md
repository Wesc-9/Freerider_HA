# Freerider HA 0.8.2 — Open the exact car from a notification

This update addresses the reported issue where tapping a car alert opened only the general Freerider homepage.

## What changed

- **Individual-car links:** The official Freerider booking-flow JavaScript supports a URL hash containing the actual route `id` and a pickup `date`. New car alerts now use the same provider-recognized parameters.
- Norwegian offers open the official `/booking-flow/no-no/` page and Swedish offers open `/booking-flow/sv-se/`, with the matching offer ID.
- We select a pickup time from the provider's published availability, return-time limit, estimated trip duration and pickup station opening hours. Stale or incomplete offers fall back to the public listings instead of a fabricated checkout link.
- **Test notification:** When a real matching car is available, the existing test button previews that car; tapping the test alert now uses its actual booking link. If no matching car is available, the test only validates mobile notifications.
- **Device & dashboard:** Per-car entity links and dashboard ride attributes now use the same car-specific URL.
- Automated matching and rich push details (car model, route, km, drive time, optional Norwegian toll estimate) remain unchanged.

## Important limitations

This is an **unofficial** integration and the deep-link format was verified from the provider's publicly served web JavaScript and the booking-flow pages, not from a published deep-link API contract. We verified both provider pages respond and their code reads the car ID/date fields. We have **not** verified a logged-in, end-to-end mobile booking; the provider may require login or reject an expired offer or exceptional pickup time. Opening a booking form does not reserve a vehicle.

The link is a direct link to that specific offer's booking process **when the provider validates its time and availability**, not a guarantee the vehicle can still be booked.

Update to **0.8.2** in HACS, restart Home Assistant, and send a test notification while at least one real Freerider offer is matching your search.
