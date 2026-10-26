# Freerider HA 0.8.1 — Available cars directly under Devices

Previously, the **Devices** page only showed **Matching rides: 2** and the raw details of the two cars were buried in attributes. The prettier offer cards were only available on dashboards.

### Now both cars appear directly on their Freerider search device
For example, the sensor list can show:

- **VW CRAFTER 14M3 4MOTION TDI VA · OSLO LUFTHAVN** — Trondheim lufthavn → Oslo lufthavn
- **VW CRAFTER 14M3 4MOTION TDI VA · OSLO ALNABRU** — Trondheim lufthavn → Oslo Alnabru

Vehicle names are taken **exactly** from the official data feed (not replaced with a generic "van" label). The destination suffix distinguishes offers with the same vehicle model.

Tap an offer sensor to see the route, published kilometers and estimated travel time, available-from and latest return dates, any verified toll estimate, and the official provider website URL.

### Dynamic and bounded
- New offers show up as new sensors without a restart.
- Once an offer disappears from the successful source refresh it is removed from the entity list/registry; stale entries after restart are cleaned up on the next successful refresh.
- When the data provider fails, sensors become unavailable rather than incorrectly reporting zero cars.
- To avoid clutter the device displays the first **8 active offers**; **Matching rides** retains the complete real count and original entity ID.
- Technical toll diagnostics moved to their own device section.
- Existing dashboard card stays optional; the Home Assistant native Devices page uses standard entity rows, not large custom cards.
- No additional external API requests or polling changes.

### Upgrade
Install **0.8.1** via HACS and restart Home Assistant. Open **Settings → Devices & services → Freerider HA → Devices → your saved search**. The extra car sensors will be added from current matching listings.

**Disclaimer:** Unofficial community project, not affiliated with or approved by Hertz. These are published offers; final booking availability is confirmed only on the official Freerider website.
