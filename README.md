# Hertz Freerider for Home Assistant

> **Alpha / development scaffold. Not yet a working availability monitor.** The Home Assistant setup UI, multi-country route/date/vehicle filters, refresh button, event/notification wiring and test framework are implemented. **No verified, authorized live Hertz listing adapter exists yet**: therefore the availability sensor deliberately reports **unavailable**, not 0, and no live-car notifications can be emitted. Do not install this expecting live listings.

Independent community project; not affiliated with or endorsed by Hertz.

## Target capabilities

- Multiple independent watch profiles (each one a Home Assistant config entry).
- Countries: **Norway, Sweden, Denmark** (the currently confirmed Freerider-specific services), multi-select. This list is extendable after official verification of additional countries; regular Hertz rental locations are not automatically Freerider countries.
- Origin and destination free-text filters, either strict direction or **either direction**; leave either blank to match any location.
- Travel date: **any**, **one day**, or **inclusive range**. Matches a known listing's pickup/booking window; when dates are missing from source, restricted-date matches are excluded rather than guessed.
- Transmission: **any**, **automatic**, **manual**. Optional vehicle type (car/van/minibus), fuel type, and minimum seats; unknown listing metadata does not masquerade as a match.
- **Automatic** background polling (minimum 15 minutes, configurable 15–120 min) or **manual** via a refresh button or `hertz_freerider.refresh` service.
- A Home Assistant count sensor with matched ride details and booking links, plus an event for genuinely new matching rides (once a source is operational). New-ride IDs are persisted locally to avoid duplicate push notifications on restart.
- English and Norwegian UI translations; event automation blueprint for notifying any phone using a Home Assistant notification service.
- No Hertz credentials requested or stored; no scraping or invented API URLs.

## Install for development only

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
| Norway | https://hertzfreerider.no/ | **Not implemented** |
| Sweden | https://hertzfreerider.se/ | **Not implemented** |
| Denmark | https://hertzfreerider.nu/ | **Not implemented** |

Swedish/Norwegian sites and Danish site have different web implementations. No country should be labeled as live until verified. Country filtering applies to the listing's source, and **does not prohibit international route destinations**.

## Roadmap / release gates

1. Establish reliable and **permitted** structured data access from each official service; validate Hertz terms and rate limits.
2. Build per-country source adapters, stable offer IDs, exact pickup windows, stations, booking URLs, vehicle metadata. Do not infer transmission/fuel/dates from vague model names.
3. Test live listings and duplicate suppression, including new matches after route/date option changes.
4. Add end-to-end Home Assistant integration tests, locale-specific station selection after source discovery and HACS beta release.
5. Consider additional countries only when a Freerider-specific service is verified.

The integration has no live source today. This limitation is intentionally visible instead of pretending to return valid search results.

## Developer checks

```bash
PYTHONPATH=custom_components/hertz_freerider python -m unittest discover -s tests -v
python -m compileall -q custom_components/hertz_freerider
```
