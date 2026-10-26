# Freerider HA

## What's new in 0.9.0 — six practical improvements

All enhancements are opt-in or conservative by default and preserve existing watch profiles.

**1. Smarter notifications:** set **Notify on existing offers on first scan** and **Notify on changes to offer dates** under **Configure → Refresh interval and events**. New, updated and removed offers are recorded in a bounded local history (100 entries). Date-change alerts are on by default; initial existing-offer alerts are off to avoid a flood. A previously absent offer triggers a new alert when it returns. Existing saved event automations retain the **new-ride** event; date updates use a separate `hertz_freerider_offer_updated` event.

**2. Better booking links:** Car links use the provider's per-offer booking flow only when a future pickup slot can be constructed from the official route ID, availability window, drive duration, return deadline and station hours. Offers from a failed source remain visible with a **stale** warning instead of pretending they can be immediately booked. Alerts from a stale source are deferred until it recovers. A real booking still requires the provider's own verification and login; it is never reserved by this integration.

**3. Car-model filters:** **Configure → Vehicle preferences** now includes **Include models** and **Exclude models**. Separate multiple partial names using `;` (for example `Crafter; Transporter`). Exclusions override inclusions. Previously saved vehicle filters remain unchanged.

**4. Partial journey cost:** **Configure → Trip cost assumptions** accepts your own fuel consumption/price (litres per 100 km, NOK per litre) and EV consumption/price (kWh per 100 km, NOK per kWh). All values default to **0 = unknown**; no price or model energy usage is guessed. The per-car sensor, dashboard and phone alerts show known toll costs, estimated driving energy and a **partial subtotal** if available. Ferries and actual rental fees are never treated as included, and unknown values are not shown as zero. Norwegian toll estimates remain quota-limited.

**5. GPS station radius:** **Configure → Search radius around stations** lets you select **25 / 50 / 100 km** around a departure or destination station from the locally remembered, provider-confirmed GPS stations. Straight-line distance is used, *not road driving distance*. Radius matches are added to your existing text station choices. Set radius to Off to disable it. Areas without verified station coordinates are not silently accepted as matches.

**6. Search status and history:** A new **Search status** diagnostic sensor groups with each saved watch. It shows last attempted and successful source scan, approximate next scan, partial/outage state, recent additions/updates/removals, number of successful and pending push notifications, and last delivery error. The existing matching-offers sensor exposes the recent history and partial travel costs. On a partial provider outage, affected cached offers remain visible with a stale status.

### Updating

Use HACS to download **0.9.0**, restart Home Assistant and open **Settings → Devices & services → Freerider HA → Configure**. All optional new screens appear there. No need to delete or recreate existing search profiles. The **Search status** diagnostic sensor is under each Freerider search device. The Lovelace resource now uses `/freerider-ha/freerider-rides-card.js?v=0.9.0`.

This is a community integration and not affiliated with or endorsed by Hertz. Exact end-to-end booking is subject to the provider's validation. Home Assistant production-runtime and physical-phone verification still require user testing.


[Latest GitHub release](https://github.com/Wesc-9/Freerider_HA/releases/latest) · [Changelog](https://github.com/Wesc-9/Freerider_HA/blob/main/CHANGELOG.md)


> **Community test integration.** Norway/Sweden live read-only feeds are connected; end-to-end Home Assistant runtime testing is still needed. Denmark is not yet implemented. Please verify booking details on Hertz before relying on any alert.

Independent community project; not affiliated with or endorsed by Hertz.

## Simpler results directly on the device page (0.8.1)

The integration now creates **one normal Home Assistant sensor per currently visible car offer** under your Freerider search device. For example, a two-offer search lists separate sensor rows:

- **VW CRAFTER 14M3 4MOTION TDI VA · OSLO LUFTHAVN** — state: `TRONDHEIM LUFTHAVN → OSLO LUFTHAVN`
- **VW CRAFTER 14M3 4MOTION TDI VA · OSLO ALNABRU** — state: `TRONDHEIM LUFTHAVN → OSLO ALNABRU`

The full car name is taken **verbatim** from the provider's original model field. Tap an individual car sensor to inspect departure, destination, distance, estimated drive duration, availability and return deadline, estimated toll if known, and the official Freerider website URL. This is the standard **Home Assistant device view**, not only a separate dashboard.

As new listings match your saved search they appear automatically; when the provider no longer lists an offer, its sensor and registry entry are removed. A failed feed update does not silently erase the last offers or pretend the count was zero: sensors become unavailable as normal. The device view is **capped at eight active offers per search** to prevent unnecessary entity proliferation. The existing **Matching rides** total counts *all* matching offers and retains its original entity ID and attributes for compatibility; the dedicated dashboard card can present the first 20. A toll-estimate diagnostic sensor is moved to the device's diagnostic section for less clutter.

**Important:** A sensor's state does not reserve a car. Final bookability and terms must be checked on the official Freerider site. Home Assistant's built-in device page supports normal sensor rows rather than custom large offer cards; the optional dashboard card remains available for richer layout and external link buttons.

## Optional visual card on a Home Assistant dashboard (0.8.0+)

The default Home Assistant entity-details dialog shows the `rides` sensor as raw attributes. Freerider HA now adds an **optional dashboard card** for an understandable list of offers, without changing how the existing sensors and alerts work.

In each offer card, the **full vehicle name is shown verbatim** from Freerider's published `carModel` field — for example **VW CRAFTER 14M3 4MOTION TDI VA**. It is **not shortened to "Crafter" or replaced with "varebil"/"van"**. The technical van classification is used *only behind the scenes* to avoid assuming an unsupported passenger-car toll tariff. The dashboard also shows the full route, provider distance, estimated driving time, availability/return deadlines, toll status, and the official Freerider website link.

**To add to a dashboard:**

1. Update to **0.8.0** through HACS, then restart Home Assistant.
2. Open any Dashboard → Edit dashboard → Add card → **Manual (YAML)**.
3. Paste (replace the entity ID if your search has a custom name):

```yaml
type: custom:freerider-rides-card
entity: sensor.freerider_matching_rides
```

The integration attempts to register the JavaScript dashboard resource in the normal storage-managed Lovelace mode. If you see **Custom element doesn't exist**, add a dashboard resource manually under **Settings → Dashboards → Resources** (or in YAML mode's `lovelace:` resources) as **JavaScript module** with URL:

```text
/freerider-ha/freerider-rides-card.js?v=0.9.0
```

The card follows Home Assistant's selected **light/dark theme** and adapts to mobile widths. There is no external frontend package, login, or extra network request. It renders existing Freerider sensor attributes and updates when that sensor changes.

**Important:** Home Assistant's standard entity detail dialog remains unchanged. Use the dashboard card for the richer results view. Clicking a current eligible car opens the official booking flow for its offer ID and proposed pickup time. When a direct link is not available or the source is stale, it opens the official country listing instead. Neither action reserves a car.

## Direct notifications with booking-site link

During **new Freerider search registration**, the **From / To / Dates** screen now also contains **Notify me about new cars** (toggle) and **Send notifications to** (a dropdown of actual Home Assistant Companion app phones, plus an in-app notification option). Select your phone and turn on notifications before submitting the search. For existing searches, open **Settings → Devices & services → Freerider HA → Configure → Places, dates and notifications**; the same controls are available there. Update frequency and Home Assistant event options remain under **Refresh interval and events**. Available phone-specific `notify.mobile_app_*` services are discovered automatically and shown by name; alternatively choose **Home Assistant notifications** for messages in the HA UI. `Off` disables direct notification, while the existing new-ride event/automation blueprint still works. Automatic checks can be enabled or disabled independently.

Notifications are sent only when **new matching cars** appear after the first successful scan. Each alert now includes the **departure → destination route, exact listed vehicle name, Freerider's advertised distance in km and estimated driving time**, earliest pickup availability, offer expiry, latest return deadline, and an optional Norwegian toll estimate. Driving time is Freerider's advertised estimate, **not** a live traffic ETA. If a field is missing it is omitted or clearly marked unavailable, never fabricated. Tapping a mobile push opens the **provider's booking-flow page for the exact route ID**, with a proposed pickup date selected from the published available period and station hours. The provider still validates the time, availability and login before booking. The public route API does not expose a ready-made per-car URL, but the official website's JavaScript accepts `#id=...&date=...` on its localized `/booking-flow/` page. The integration creates the link using the provider's own fields. This link is **not** a reservation, and the provider may redirect if the car has expired or requires an unavailable pickup time.

Use the **Test notification** button on your Freerider search device (all controls now appear under one device instead of Ungrouped) to preview a real matching car's detailed alert (clearly marked **TEST**) and verify that the selected phone works. No external toll lookup is performed just to render a test alert. The **New car alerts** switch on the same device lets you pause/resume direct notifications without losing the chosen phone. Choosing a phone turns alerts on automatically. Errors or disconnected phones do not stop route updates; failed alerts can retry on later successful scans while the car is still matching. Up to eight phone alerts per scan are attempted to avoid a notification storm; remaining alerts are queued for a later successful refresh.

This integration is unofficial and not associated with Hertz. Tolls and fuel/charging costs may apply.

## Automatically learned stations

The origin/destination dropdown combines live stations with a **local Home Assistant-wide history** of stations seen on earlier scans. The same existing 15–120 minute route scans automatically add new stations, regardless of whether they match a saved search. Previously discovered stations remain selectable when listings expire and after Home Assistant restarts. Station history is stored **locally** by Home Assistant; it is not uploaded to a community-wide database or bundled with the GitHub repository. Other installations learn their own stations independently.

Selected places are removed from the suggestions when reopening a search form. Home Assistant's built-in multi-select handles selections inside an already open dropdown; the integration cannot force the UI to update its choices without reloading the form. Likewise, native date picker closing behavior is controlled by the Home Assistant frontend and cannot be overridden by a backend integration. The date inputs remain the native HA date controls.

## Simple, bilingual setup (Norwegian / English)

The current Home Assistant setup is a **2-step native wizard**:

1. **Name and countries** — select Norway and/or Sweden. Denmark is listed as coming later.
2. **From / to and dates** — select *several* stations in each input, or type custom station names. The integration monitors any chosen departure → any chosen arrival combination. Leave an input empty to match anywhere. Choose no dates (all), only the first date (one day), or both dates (an inclusive range).

After setup, use **Settings → Devices & services → Freerider → Configure** to independently edit **Places and dates**, **Dates**, **Optional vehicle filters**, or **Automatic checks and notifications**. Existing searches are editable; no need to delete and start over. Automatic polling defaults to 30 minutes. Multiple saved routes work as separate integration entries.

The integration follows the user's Home Assistant **light/dark theme**; it cannot impose a separate bright design over the native Home Assistant modal. Configure Home Assistant to use Light appearance for the Apple-like, neutral look. The source UI follows the Home Assistant locale and includes Norwegian Bokmål (`nb`) and English (`en`) translations.

The public integration name is **Freerider HA** (no Hertz branding in the title). The internal Home Assistant domain remains `hertz_freerider` to retain existing installation and entity IDs.

This is an **independent, unofficial community project**. It is not developed, operated, sponsored, licensed or endorsed by Hertz. Hertz and Freerider names are used solely to identify the supported service; do not mistake this project for an official integration.

## Target capabilities

- Multiple independent watch profiles (each one a Home Assistant config entry).
- Countries: **Norway, Sweden, Denmark** (the currently confirmed Freerider-specific services), multi-select. This list is extendable after official verification of additional countries; regular Hertz rental locations are not automatically Freerider countries.
- Searchable multi-select departure/arrival inputs (with typed free-text options). Choose several origins and several destinations in one saved search. All combinations match; empty means anywhere. Both-direction matching is optional.
- Travel date: **any**, **one day**, or **inclusive range**. In NO/SE, matches from published availableAt through offer expireTime. This is NOT a guaranteed selectable pickup window. Missing dates are excluded.
- Transmission: **any**, **automatic**, **manual**. Optional vehicle type (car/van/minibus), fuel type, and minimum seats; unknown listing metadata does not masquerade as a match.
- **Automatic** background polling (minimum 15 minutes, configurable 15–120 min) or **manual** via a refresh button or `hertz_freerider.refresh` service.
- A Home Assistant count sensor with matched ride details and booking links, plus an event for genuinely new matching rides (once a source is operational). New-ride IDs are persisted locally to avoid duplicate push notifications on restart.
- English and Norwegian UI translations; event automation blueprint for notifying any phone using a Home Assistant notification service.
- No Hertz credentials requested or stored. The NO/SE read-only JSON paths were discovered in the published Freerider frontend and tested with HTTP 200 responses. No secret/private endpoints are used.

## Install via Home Assistant (HACS, community test release)

**1. Add/open the GitHub repository directly in HACS:**

[![Open Freerider_HA in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Wesc-9&repository=Freerider_HA&category=integration)

This official *My Home Assistant* link opens the repository in the user's own instance, including HACS custom repositories. HACS must be installed. **Clicking the badge does not silently install anything**: choose Download/Install inside HACS and restart Home Assistant when prompted.

**2. Add the integration after installation:**

[![Set up Freerider HA](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=hertz_freerider)

Or use Settings → Devices & services → Add integration → Freerider HA.

**Alternative manual installation:** copy `custom_components/hertz_freerider` into `<config>/custom_components/`, restart Home Assistant, and add the integration.

When installed, configure any number of independent watched routes, date ranges, vehicle preferences and country sources. Norway/Sweden public route adapters are active; Denmark still requires a validated feed. Existing profiles can be edited in **Configure**. This remains alpha until tested against a real Home Assistant runtime.

### Extra costs (important)

**Tolls may be charged to the driver. Fuel/charging costs may apply.** Check the actual country's Freerider conditions and the booking terms before reserving. The FreeRide transfer is not necessarily an entirely free journey. For Danish Freerider, Hertz's FAQ says the first full tank is included, extra fuel may be paid by the driver and bridge/ferry fees normally fall to the driver; verify exceptions directly in the booking. For Norway, Hertz says regular toll tariffs are charged to the rental customer without transferring the normal AutoPASS discount.

**Norwegian toll estimate (automatic in new alerts + manual button):** For **new matching Norwegian person-car offers**, the integration makes a best-effort route toll estimate using the real pickup/drop-off coordinates and BompengeAppen's documented API. The estimated cost is displayed in the mobile push, clearly marked as an estimate. An optional switch **Include estimated tolls in new car alerts (Norway)** is available under **Configure → Refresh interval and events** and defaults on. To avoid exhausting the keyless provider's limit of 100 calls per IP per day, Freerider HA caps automatic lookups to **10 per day per Home Assistant instance** and **two fresh estimates per scan**, shared by all saved searches. Successful estimates are cached locally for 20 hours across Home Assistant restarts. If quota, timeouts or coordinates make a reliable price impossible, the new-car push still goes out immediately after the attempt with **"Toll estimate unavailable"**, never a made-up zero. International/Swedish trips are labeled outside the current Norwegian toll coverage; larger vehicles with uncertain weight classes are not priced as ordinary passenger cars.

Manual route pricing remains available through **Estimate toll for first match** and `hertz_freerider.estimate_toll` using an exact `entry_id` and `ride_id`. Manual calls use the provider's separate standard access policy and are not counted in the Freerider HA automatic estimate allowance; they may still consume the provider's daily quota.

**Route metrics:** Freerider's actual `distance` (kilometres) and `travelTime` (minutes) fields are used in the alert. The toll calculator may also supply its independent distance and duration for a proposed road route, but does not replace Freerider's own advertised estimates.

Estimates use **without-AutoPASS-discount** tariffs to better reflect Hertz's Norway FAQ; they **are not the final amount Hertz will invoice** and may differ due to VAT, fees, vehicle category, seasonal tariffs, time of day or deviations from the proposed road route. For an EV, the no-discount EV rate is used when explicitly identified. Ferries, bridges or journeys outside Norway are **not quoted as zero**: they're labeled unknown/not included. The calculation defaults to the current time unless an ISO `start_time` is provided (e.g. `2026-10-27T08:30:00+01:00`). A user-triggered request can consume quota at BompengeAppen.

**Provider verification:** a single documented API request on 2026-10-26 returned HTTP 200, route pricing with `tollSmallNoDiscount` and `tollSmallEvNoDiscount`, and charged-station details. This validates the API response format, **not** a successful end-to-end Home Assistant installation.\n\n**Data used:** [BompengeAppen API docs](https://bompengeappen.no/api-docs), [Hertz Norway FAQ](https://www.hertz.no/p/faq), [Hertz Denmark FAQ](https://hertzfreerider.nu/ofte-stillede-sporgsmal/).

### Refresh service

```yaml
action: hertz_freerider.refresh
data: {}
```

Refreshes every configured profile. Optionally pass `entry_id` to refresh just one; or press the profile's **Refresh Freerider listings** button.

### New-ride event (after source integration)

`hertz_freerider_new_ride` is emitted when a **new ride identity** matches an active profile after the initial baseline. Event contains `entry_id`, `watch_name`, `origin`, `destination`, `vehicle`, `country`, `transmission`, `date_start`, `date_end`, and `booking_url`.

Import the optional blueprint using the path above; select your mobile notification service. The builtin direct-notification feature needs only a selected Home Assistant Companion app and the **Notify me about new cars** toggle during registration. An optional event blueprint is still available for advanced automations.

## Confirmed Freerider services

| Country | Site | Adapter |
|---|---|---|
| Norway | https://hertzfreerider.no/ | **Public JSON API connected; HA runtime test pending** |
| Sweden | https://hertzfreerider.se/ | **Public JSON API connected; HA runtime test pending** |
| Denmark | https://hertzfreerider.nu/ | **Not implemented** |

NO and SE expose public read-only `/api/transport-routes/?country=NORWAY` and `?country=SWEDEN` endpoints, returning grouped route offers. The Danish catalog is JS-rendered and can list products that are out of stock. No country should be labeled stable until end-to-end testing. Country filtering applies to the listing's source, and **does not prohibit international route destinations**.

## Roadmap / release gates

1. Validate Hertz permitted automated API use and polling limits. Confirm live Home Assistant behavior for the implemented NO/SE feeds, then seek a permitted Danish route source.
2. Improve country adapters, especially exact pickup cutoff vs offer expiry, stations, booking deep links and vehicle metadata. Only derive transmission/fuel from explicitly labeled text.
3. Test live listings and duplicate suppression, including new matches after route/date option changes.
4. Add end-to-end Home Assistant integration tests, locale-specific station selection after source discovery and HACS beta release.
5. Consider additional countries only when a Freerider-specific service is verified.

Important date caveat: \`availableAt\` is when the car becomes available, \`expireTime\` is the offer expiration, and \`latestReturn\` is the return deadline. Selecting a date filters the advertised offer window but does **not** guarantee Hertz will allow pickup on every matching day. Confirm exact pickup time on the booking site. The integration is not affiliated with Hertz.

## Developer checks

```bash
PYTHONPATH=custom_components/hertz_freerider python -m unittest discover -s tests -v
python -m compileall -q custom_components/hertz_freerider
```
