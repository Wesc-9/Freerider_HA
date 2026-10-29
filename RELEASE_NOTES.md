# Freerider HA 0.10.2 — date fields work in registration

## Fixed
- **From date and To date are now usable on the same registration/configuration screen.** Previously they were always marked `read_only=True`, even after switching **All dates** off.
- **All dates ON** (default): No date limit; any entered dates are intentionally ignored and cleared when saved. **All dates OFF**: Choose a from date and optionally a to date directly, without being sent through more forms. A missing from date or an end before start is rejected with a clear form error.
- Norwegian and English labels now explain that date inputs apply only when All dates is OFF.
- The **New car alerts** switch remains independent. To get push notifications at any date, turn on notifications and select a registered phone.

## Why are the inputs not greyed out when All dates is ON?
On Home Assistant Core 2026.10 and earlier, config-flow fields cannot be enabled/disabled live based on another field's switch. Rather than making the fields permanently read-only as in 0.10.1, **0.10.2 makes them editable** and treats All dates as authoritative when saved. Dynamic conditional config-flow fields are planned for Home Assistant 2026.11. This compatibility fix ensures you can actually choose dates today.

## Install
Update through HACS to **0.10.2**, restart Home Assistant, then open **Add service** or edit your Freerider search under **Configure → Places, dates and notifications**.

Existing searches, radius sliders, pause switch, mobile alerts, sensors and saved settings are preserved. Automated CI tests passed, but this form interaction still needs a final check in the actual Home Assistant mobile app.

Independent community project, not affiliated with Hertz.
