# Changelog

## 0.9.0 (2026-10-26) — comprehensive search, alerts and diagnostics
- Smarter alerts: optional existing offers on first scan, default alerts on date changes, and notifications for confirmed returned offers.
- Local 100-event history of newly seen, updated and removed offer IDs; no false removal when a country feed is down.
- Better offer-link status and stale-source guards; no push alerts based solely on stale cached offers.
- Model name include/exclude filters using case/accent-insensitive semicolon-separated terms.
- 25, 50 and 100 km radius around GPS-known source stations (straight-line), with coordinates stored across restarts.
- Four user-configurable price/consumption assumptions for a clearly marked partial fuel/charging/toll cost breakdown; no invented complete totals.
- New diagnostics sensor: source health, successful/attempted checks, next estimated check, pending/sent alerts, and recent offer activity.
- Updated Lovelace card with partial cost sections and safe official booking actions; refreshed frontend asset version.
- Expanded regression tests for stable notifications, reappearing offers, mixed-source failures and electric fuel costs.


## 0.8.2 (2026-10-26) — booking-flow deep links for exact cars
- Fixed push alerts opening only the Freerider homepage: directly open provider booking-flow for the matching official route ID and selected pickup date.
- Confirmed official NO/SE booking page paths and hash parameters from the provider's public JavaScript.
- Pick a future pickup time within published offer availability, closing/return limits and pickup station weekday hours.
- Use safe fallback for incomplete/expired data. This is not an authenticated end-to-end booking guarantee.
- Apply links to both mobile notifications and Home Assistant per-car sensors/dashboard payloads.
- Test alerts use the selected real matching car when one exists, while generic tests are explicitly marked.
- Added unit tests for specific links, time selection, country routes, validity and safe fallback.
- Removed the temporary web research workflow.


## 0.8.1 (2026-10-26) — active offers in the device view
- Surface one normal sensor per currently matched car offer directly on the Freerider HA device page.
- Each row names the exact provider car model plus return destination; its state gives the origin → destination route.
- Tapping a car sensor shows its dates, time, kilometers, model, toll status and official provider link.
- On successful refresh, dynamically add new car-offer sensors and remove vanished ones, including stale entity-registry entries after restart.
- During a source failure retain existing entities as unavailable; do not falsely report zero offers.
- Cap per-search visible device offer sensors at 8; retain the full real count and original aggregating sensor ID.
- Move the last toll-estimate sensor to diagnostics to reduce the primary sensor list.
- Original dashboard card remains available when a user wants richer visual presentation.
- No new calls to the Freerider data sources; uses already fetched coordinator data.


## 0.8.0 (2026-10-26) — readable offers and exact car model names
- Optional Home Assistant dashboard card shows separate offer cards rather than raw sensor attribute lists.
- Original provider `carModel` string displayed prominently and unmodified (including VW CRAFTER 14M3 4MOTION TDI VA).
- Show actual route, provider distance, duration, pickup availability, return deadline, current toll estimate, and official Freerider listing link.
- Recognize VW Crafter and other known cargo-van models internally, but **never** replace their visible car model with a derived generic vehicle type.
- Block automatic and manual small-passenger-car toll pricing when van/minibus weight or toll class is unverified; do not misrepresent an unavailable price as zero.
- Preserve existing matching-rides sensor ID, entity attributes, configured searches and mobile alert routing.
- Register optional dashboard JavaScript resource in storage mode; document manual resource setup fallback.
- Add frontend syntax checking and unit test coverage for true car model preservation.


## 0.7.0 (2026-10-26) — detailed journey alerts
- Parse real Freerider distance (km) and drive time (minutes), include along with vehicle model, route and date deadlines in push messages.
- Use real station coordinates for optional Norwegian toll estimates on new matching car alerts.
- Shared per-installation daily limit (10) and per-scan fresh-lookup cap (2); persisted 20-hour quote cache.
- Fail-open notification: never suppress new car alerts when toll API is unavailable or rate-limited.
- Accurate no-AutoPASS-discount quote or explicit unsupported/unavailable label; never show invented zero.
- Separate estimates from Freerider drive distance/time; no claim of live driving ETA.
- Test notification previews a real car with the rich alert layout, clearly marked test.
- Norwegian and English messages, controls and regression tests.


## 0.6.2 (2026-10-26) — select phone and notifications during registration
- Added **Notify me about new cars** toggle and **Send notifications to** mobile dropdown directly to the new search's From/To/Date screen.
- Warns before submission when notifications are enabled without a receiving device.
- Existing searches can set or change the exact same controls under Configure → Places, dates and notifications; no deletion required.
- The Home Assistant New car alerts switch remains synchronized, so you can later pause/resume without reentering setup.
- The separate refresh/events configuration no longer duplicates notification-recipient selection.
- Norwegian and English labels and validation included. All existing Freerider data and search profiles remain compatible.


## 0.6.1 (2026-10-26) — easy notification controls
- Added a dedicated **New car alerts** switch for each saved watch in Home Assistant.
- Added the **Test notification** button to verify your selected phone.
- Groups every watch's sensor(s), refresh, toll and notification controls under one Home Assistant device instead of "Ungrouped".
- Phone selection enables alerts automatically. Toggle can later disable them without clearing the chosen phone.
- Preserves failed mobile alerts in local storage and retries if the offer is still available.
- Limits dispatch attempts to eight per refresh to prevent large notification bursts.
- Adds tests for mobile push URLs and destination selection.


## 0.6.0 (2026-10-26) — mobile notifications and booking website links
- Choose a specific Home Assistant mobile-app notification service in the integration's existing settings UI.
- Get push alerts with route, vehicle, date and official country booking-site link when a new matching car appears.
- Added a test-notification button to make setup easy to verify.
- Default direct notifications to Off until a recipient is selected; legacy event automations remain supported.
- Initial first scan establishes a baseline. Missed push attempts can be retried if the offer stays available.
- Up to eight alerts sent per scan to avoid flooding phones; additional new matching offers are queued.
- No invented per-car deep links: current official site uses browser session state for booking selection.


## 0.5.1 (2026-10-26) — remembered stations
- A shared, local station catalog automatically records every distinct station discovered while checking the Norwegian and Swedish Freerider feeds.
- Remembered stations survive Home Assistant restarts and remain selectable after offers disappear.
- Newly discovered cities/stations become available the next time the configuration/options form opens.
- Previously selected stations are omitted from the initial available suggestions when editing, while their selected chips remain displayed.
- Selectors still support free-text multi-select for places not yet discovered.
- Does not change the frequency of existing network polling or publish a shared internet-wide database.
- Home Assistant's native frontend controls live dropdown updates and date-calendar auto-dismissal; the integration does not inject unsupported frontend code.


## 0.5.0 (2026-10-26) — multiple locations, dates in one screen and neutral branding

- Renamed the **displayed** integration to **Freerider HA** throughout Home Assistant, HACS and the README (the internal domain remains `hertz_freerider` for backwards compatibility).
- Choose multiple departure **and** arrival stations in the same searchable comboboxes; any departure is matched against any arrival.
- Supports typed station names even when missing from current Hertz station suggestions, plus a Værnes/Trondheim Airport alias.
- Added optional travel dates directly to the route step: no dates = any, first date alone = one day, first/last = a date range.
- Existing single-station search profiles continue to work; update them through Configure.
- Updated Norwegian and English UI copy and independent-service disclaimers.
- Release tag `0.5.0` without a leading `v` for straightforward HACS version identification.


## v0.4.0 (2026-10-26) — community test release
- New native guided setup for countries, locations and dates.
- Station suggestions with optional free-text search.
- Norwegian and English translations.
- Advanced filtering and alert preferences moved to configuration submenus.
- Working public route feeds for Norway and Sweden.
- Manual toll estimation for Norwegian routes and clear extra-cost notices.
- Independent project disclaimer and HACS install instructions.
- GitHub release and HACS version publishing automation.

### Known gaps
- Denmark feed unavailable.
- Exact booking times and Home Assistant runtime behavior require broader field testing.
- Full HACS publish validation requires repository Topics metadata.
