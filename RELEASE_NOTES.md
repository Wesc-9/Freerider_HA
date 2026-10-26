# Freerider HA 0.7.0 — richer car alerts and automatic Norwegian toll estimates

## Your mobile alert now includes
- **From → to**: actual Freerider departure and arrival stations.
- **Vehicle**: the original car model/name, not a generic vehicle class.
- **Distance and journey time**: published Freerider kilometres and estimated driving minutes.
- **Dates and deadlines**: available-from time, offer expiry and latest allowed return if provided.
- **Norway road tolls**: best-effort estimated NOK using no-AutoPASS-discount passenger-car tariffs.
- **Fuel/charging notice**, plus the offer ID and an official provider-site link that opens when the push is tapped.

## Toll calculation — safe and transparent
- Uses BompengeAppen's public route calculator from real Freerider station coordinates for eligible domestic NO→NO passenger-car routes.
- Quota-aware: maximum **10 new automatic lookups per day for the entire Home Assistant installation** and **2 fresh lookups per feed scan**, reusing a 20-hour persistent cache for repeated station pairs.
- Calculation can take time and may fail or be limited. **New car alerts are delivered anyway** with an explicit unavailable/unsupported toll status, never a fabricated 0 kr.
- Car fuel category/weight, toll scheme, time of day, ferries and the road route can change final charges.
- Swedish/cross-border trips and uncertain heavy-vehicle classes don't receive a misleading Norwegian car toll quote.
- Toggle automatic toll estimates on/off under Configure → Refresh interval and events.

## Test notification
If the watch has a real matching car, pressing **Test notification** previews the complete expanded alert for that car, clearly labeled as a **test**, without spending toll-API calls. Otherwise it sends a simple connectivity test.

## Important
This is **Freerider HA**, an unofficial community integration, not affiliated with Hertz. The notification opens the official Freerider website for that country, **not an unverified direct checkout/deep link for a specific car**. Confirm actual car availability and booking conditions before traveling.

The setup supports Norway and Sweden; Denmark data source remains pending. End-to-end delivery on a real user's phone should still be validated.

## Updating
Install **0.7.0** in HACS, restart Home Assistant, then use the Test notification button on your search device.
