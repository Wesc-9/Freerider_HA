# Hertz Freerider for Home Assistant

> **Developer alpha: live Norway/Sweden feeds connected, Home Assistant runtime not yet tested.** Verified public Hertz route JSON endpoints returned real offers without login on 2026-10-26. Denmark is listed in setup but has no working adapter. Do not rely on mobile notifications until end-to-end testing.

Independent community project; not affiliated with or endorsed by Hertz.

## Target capabilities

- Multiple independent watch profiles (each one a Home Assistant config entry).
- Countries: **Norway, Sweden, Denmark** (the currently confirmed Freerider-specific services), multi-select. This list is extendable after official verification of additional countries; regular Hertz rental locations are not automatically Freerider countries.
- Origin and destination free-text filters, either strict direction or **either direction**; leave either blank to match any location.
- Travel date: **any**, **one day**, or **inclusive range**. In NO/SE, matches from published availableAt through offer expireTime. This is NOT a guaranteed selectable pickup window. Missing dates are excluded.
- Transmission: **any**, **automatic**, **manual**. Optional vehicle type (car/van/minibus), fuel type, and minimum seats; unknown listing metadata does not masquerade as a match.
- **Automatic** background polling (minimum 15 minutes, configurable 15–120 min) or **manual** via a refresh button or `hertz_freerider.refresh` service.
- A Home Assistant count sensor with matched ride details and booking links, plus an event for genuinely new matching rides (once a source is operational). New-ride IDs are persisted locally to avoid duplicate push notifications on restart.
- English and Norwegian UI translations; event automation blueprint for notifying any phone using a Home Assistant notification service.
- No Hertz credentials requested or stored. The NO/SE read-only JSON paths were discovered in the published Freerider frontend and tested with HTTP 200 responses. No secret/private endpoints are used.

## Install for development / personal testing (not stable)

Copy `custom_components/hertz_freerider` into `<config>/custom_components/` and restart Home Assistant. Add **Hertz Freerider** under **Settings → Devices & services → Add integration**. Use **Configure** to modify filters. Create additional integration entries for more saved routes.

The source adapters in `source.py` intentionally raise a visible source-not-implemented error. Once an authorized country feed is available, implement the adapter and normalize its output to `Ride` records. The sensor will then become available, and new-ride events can be used with the supplied blueprint (`blueprints/automation/hertz_freerider/new_ride.yaml`).

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

NO and SE expose public read-only \`/api/transport-routes/?country=NORWAY\` and \`?country=SWEDEN\` endpoints, returning grouped route offers. The Danish catalog is JS-rendered and can list products that are out of stock. No country should be labeled stable until end-to-end testing. Country filtering applies to the listing's source, and **does not prohibit international route destinations**.

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
