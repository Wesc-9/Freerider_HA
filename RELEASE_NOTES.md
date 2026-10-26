# Freerider HA 0.6.0

You can now choose a recipient and receive notifications **directly from Freerider HA** when a new matching car appears — no separate Home Assistant automation required.

### New
- Choose your Home Assistant Companion app iPhone/Android under **Configure → Automatic checks and notifications**.
- A push message includes origin → destination, vehicle, date, and offer ID.
- Tapping the push opens the correct official Freerider country website to find and book the displayed offer.
- **Test notification** button available in Home Assistant entity list.
- Existing event-based automations still work. Messages on the first feed scan are skipped to avoid alert floods.
- Notification errors do not break the route sensor; unsuccessful notifications can retry later if still available.

### Important booking-link limitation
The public Norway/Sweden API currently does not expose a verified deep link for an individual vehicle. This release opens the provider's correct booking website, **not** the exact car's checkout screen. The message contains the route and offer ID so you can identify the advertised vehicle. Do not assume a car is reserved until Hertz confirms it.

This is an unofficial community integration, not endorsed or affiliated with Hertz. Denmark feed unavailable. Tolls and fuel/charging costs may apply.

### Updating
Update to **0.6.0** in HACS and restart Home Assistant. Then select your phone in the integration configuration and press the test notification button.
