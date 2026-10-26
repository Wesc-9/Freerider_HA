# Freerider HA 0.10.0 — safer shared searches and smarter trip choices

## Six improvements

1. **Shared, rate-conscious Norwegian/Swedish feed fetching.** All saved searches on one HA server use a shared per-country snapshot (minimum 15 minutes between ordinary source requests), conditional HTTP requests with ETag / If-Modified-Since when available, and backoff on provider errors. HTTP 429/503 honors Retry-After. HTTP 403 pauses automated requests for four hours. Manual refresh is limited to one forced country fetch per five minutes; it can return locally cached data in between. Initial/default watch interval remains 30 minutes. **This is load reduction, not proof of permission** to scrape or poll public Hertz endpoints.
2. **Offer ranking.** Configure → Vehicle preferences → Sort offers by: earliest date, shortest travel time, shortest distance, nearest pickup to your HA home (straight-line only), lowest known cost (partial estimates), or greatest available time margin. A local sort menu is also available on the dashboard card.
3. **Feasibility warnings.** Each offer carries an estimated travel-margin status using provider available-from/return deadlines and driving duration, plus an assumed 30-minute pickup/return buffer. This is not confirmed pickup availability and does not account for all opening hours, traffic, or pauses.
4. **Smart alert rules.** Configure → Alert preferences and quiet hours: e.g. 22:00–07:00 Norwegian time; optional urgent override for offers expiring within three hours, estimated toll ceiling, or feasible-only alerts. Unknown toll prices do **not** pass a user-imposed toll ceiling. Quiet-hour notifications remain pending until a subsequent successful scheduled scan.
5. **Favorites and calendar.** Save individual currently matching car offers as favorites directly from the dashboard; saved metadata persists locally across HA restarts. Favorite status does NOT reserve or guarantee a vehicle. Export an `.ics` placeholder for the provider's published availability/return window, prominently labeled "NOT BOOKED". This is a calendar file download, not a direct write to a user's connected calendar.
6. **Maps.** Expand a result's OpenStreetMap geographic view and open external OpenStreetMap road directions from the offer's source station coordinates. The embedded map shows the general area, **not** an exact booked or driven road route; the external directions provider calculates a suggested road route.

### How to use
1. Update from HACS to **0.10.0** and restart Home Assistant.
2. Open Freerider HA → Configure → Vehicle preferences to select the default order.
3. Open Configure → Alert preferences and quiet hours for optional push restrictions.
4. Add or reopen the dashboard's Freerider card:

```yaml
type: custom:freerider-rides-card
entity: sensor.freerider_matching_rides
```

If the card is unavailable, register `/freerider-ha/freerider-rides-card.js?v=0.10.0` as a Lovelace JavaScript module in Dashboard Resources (replace the sensor entity ID with your search's matching-rides sensor).

### Important
- Home Assistant native entity dialogs remain native; map, card sorting, favorites and .ics export are in the **optional dashboard card**, not in the built-in entity popup.
- Existing per-car entities on the Freerider device page remain in place.
- Direct booking links are not booking confirmations. Do not assume any offer remains available until the provider verifies it.
- A real end-to-end test in a user's Home Assistant installation, including push delivery and frontend resource registration, has **not** been completed by CI.
- This is an unofficial community integration, not affiliated with or endorsed by Hertz. We have not established permission for any specific public-endpoint polling frequency.

Tests: Python regression tests, Node frontend behavioral tests and Home Assistant hassfest. HACS publication validation still needs GitHub repository Topics metadata.
