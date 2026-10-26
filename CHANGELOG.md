# Changelog

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
