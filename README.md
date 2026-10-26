# Freerider HA

[Latest GitHub release](https://github.com/Wesc-9/Freerider_HA/releases/latest) · [Changelog](https://github.com/Wesc-9/Freerider_HA/blob/main/CHANGELOG.md)


> **Community test integration.** Norway/Sweden live read-only feeds are connected; end-to-end Home Assistant runtime testing is still needed. Denmark is not yet implemented. Please verify booking details on Hertz before relying on any alert.

Independent community project; not affiliated with or endorsed by Hertz.

## Direct notifications with booking-site link

During **new Freerider search registration**, the **From / To / Dates** screen now also contains **Notify me about new cars** (toggle) and **Send notifications to** (a dropdown of actual Home Assistant Companion app phones, plus an in-app notification option). Select your phone and turn on notifications before submitting the search. For existing searches, open **Settings → Devices & services → Freerider HA → Configure → Places, dates and notifications**; the same controls are available there. Update frequency and Home Assistant event options remain under **Refresh interval and events**. Available phone-specific `notify.mobile_app_*` services are discovered automatically and shown by name; alternatively choose **Home Assistant notifications** for messages in the HA UI. `Off` disables direct notification, while the existing new-ride event/automation blueprint still works. Automatic checks can be enabled or disabled independently.

Notifications are sent only when **new matching cars** appear after the first successful scan. The message contains departure, destination, vehicle, available-from date, and the offer ID. Tapping a mobile push opens the **official Freerider website for that country**, where you can select the matching offer and complete booking. The public route API currently does **not** expose a proven, direct per-car booking URL; do not misrepresent the link as a direct reservation of that specific car.

Use the **Test notification** button on your Freerider search device (all controls now appear under one device instead of Ungrouped) to send a clearly labeled sample and verify that the selected phone works. The **New car alerts** switch on the same device lets you pause/resume direct notifications without losing the chosen phone. Choosing a phone turns alerts on automatically. Errors or disconnected phones do not stop route updates; failed alerts can retry on later successful scans while the car is still matching. Up to eight phone alerts per scan are attempted to avoid a notification storm; remaining alerts are queued for a later successful refresh.

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

## Install via Home Assistant (HACS, developer alpha)

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

**Norwegian toll estimate (on-demand):** The integration includes a manually triggered estimate based on the selected NO→NO route and its real Hertz station coordinates. It uses BompengeAppen's documented public route calculator. It deliberately does **not** call this service automatically for every route: the free keyless limit is 100 requests per IP per day, and toll estimates can vary with vehicle type, trip time and the route chosen. Use the button **Estimate toll for first match**, or call `hertz_freerider.estimate_toll` with an exact `entry_id` and route `ride_id`. Results appear under the matching rides in the sensor's attributes and in the latest estimate sensor.

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

Import the optional blueprint using the path above; select your mobile notification service. Automatic push notifications require a Home Assistant automation; they are not silently enabled.

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
