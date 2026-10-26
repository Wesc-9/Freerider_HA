# Freerider for Home Assistant — v0.4.0

First public **test release** supporting updates through HACS. This is an independent, unofficial community integration, not developed, approved, sponsored or affiliated with Hertz.

## New in this release
- A streamlined, native Home Assistant setup wizard: choose countries, from/to and travel dates.
- Norwegian Bokmål and English configuration screens (follows the Home Assistant language).
- Searchable suggestions for departure and arrival stations obtained from live published routes, with manual free-text input if a station is missing.
- Optional date/date-range filtering and editable multi-route search profiles.
- Additional vehicle filters, refresh preferences and notification event controls moved under Configure.
- Live, read-only route data for Norway and Sweden, plus stable ID matching for new results.
- Optional on-demand Norwegian toll estimates, showing the full no-AutoPASS-discount price where supported by the calculation provider.
- Notices that tolls may be charged and fuel/charging costs may apply.
- HACS installation badge, independent branding and a clear not-affiliated-with-Hertz disclaimer.

## Important known limitations
- Denmark's source is not yet implemented. At least one of Norway or Sweden must be selected.
- Dates represent the published route offer window, **not** guaranteed bookable pickup time slots.
- The toll quote is an estimate for Norwegian road routes only; ferries, fuel/charging and final provider charges are excluded.
- Automated notification events require your own Home Assistant mobile automation.
- This is a test release: Home Assistant runtime installation and all individual booking scenarios have not yet been validated.
- HACS publication validation still requires repository **Topics** in GitHub settings. Custom HACS repository installations may still work.

## Updating in HACS
1. Open HACS → Freerider / Hertz Freerider.
2. Download / Update to **v0.4.0** when HACS detects the new release.
3. Restart Home Assistant.
4. Open **Settings → Devices & services → Hertz Freerider → Configure** to use the new settings layout.

If HACS does not show the release, refresh the HACS repository information and check that `Wesc-9/Freerider_HA` was added as a custom integration repository.

Report bugs: https://github.com/Wesc-9/Freerider_HA/issues
