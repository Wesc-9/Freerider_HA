# Freerider HA 0.11.1 — «Legg til reise» directly in Home Assistant

**New setup**: The first page asks for an optional BompengeAppen API key, shared by every trip. After saving, the first **Add trip / Legg til reise** form opens automatically.

**Additional trips**: On the Freerider HA integration page, press **Legg til reise** to add a separate trip, just as in Flight Assistant. Choose its name, country, start/end places, radii, dates and notification phone. Each trip is a native Home Assistant subentry and has its own device, sensors and controls. The global API key is not shown on trip forms.

**Existing installations**: Older Freerider searches and their entity IDs remain intact. New trips are added as subentries beneath a parent search entry. No existing searches are automatically removed or converted. If you already created several Freerider entries, they can remain alongside the new trips. The first entry manages the shared API key under Configure.

**Before use**: Update to 0.11.1 in HACS and restart Home Assistant. Automated Python, HACS and hassfest tests run in GitHub, but mobile layout and real-world notifications/route checks still need verification on your instance.

Unofficial community integration; not affiliated with Hertz or BompengeAppen.
