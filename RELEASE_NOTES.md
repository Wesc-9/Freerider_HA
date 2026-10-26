# Freerider HA 0.8.0 — Clear results for matching rides

New optional **dashboard results card**: one readable card per matching Freerider offer.

## Each offer shows
- **Exact original vehicle name**, just as published by the provider — e.g. `VW CRAFTER 14M3 4MOTION TDI VA`, not a generic "van".
- Origin → destination, distance in km, estimated travel time.
- Available-from date and latest return time.
- Toll estimate when legitimately available; "Unknown vehicle toll class" for vans with unknown permitted vehicle weight.
- Safe button opening the official Freerider website for that country. No unverified per-car booking deep link.

## Technical safety fixes
- VW Crafter, Sprinter, Transit, Ducato and other commercial vehicle model names are recognized for internal vehicle classification.
- **No incorrect Norwegian small-passenger-car toll quote** for commercial vans or minibuses in automatic alerts or the manual toll estimator, unless a future release can verify the correct vehicle toll class.
- Legacy matching-rides entity ID remains unchanged; the dashboard card is entirely optional.

## Install the dashboard card
1. Update **Freerider HA to 0.8.0** in HACS and restart Home Assistant.
2. Edit a dashboard → Add Card → **Manual**.
3. Use:

```yaml
type: custom:freerider-rides-card
entity: sensor.freerider_matching_rides
```

If the card is not recognized, add `/freerider-ha/freerider-rides-card.js?v=0.8.0` as a **JavaScript module** under Dashboard Resources, then reload the dashboard. The integration attempts to register that resource automatically when Home Assistant uses Lovelace storage mode.

**Note:** This card is shown on dashboards; it does not replace Home Assistant's normal entity detail pop-up. The default sensor will continue to expose raw attributes for power users and automations.

Unofficial community project, not affiliated with or approved by Hertz. Vehicle availability and booking must be confirmed at the official website.
