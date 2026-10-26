# Freerider HA 0.9.0

A six-part update to search quality, mobile alerts and diagnostics. **Existing saved searches, Home Assistant entities and notification devices are preserved.**

## New capabilities

### Smarter notifications
- New vehicles trigger alerts after the normal first baseline check.
- Optionally alert for vehicles that are *already* available on the first scan (off by default).
- Date/availability changes to an existing vehicle can trigger an updated-offer alert (on by default).
- Confirmed removed/returned offers are recorded and returning offers can trigger a new alert.
- An outage in one country does not falsely mark its cars as removed or send stale-car alerts.

### Booking-link reliability
- Official NO/SE car-specific booking links are retained where an eligible pickup time can be constructed.
- Latest source health is shown alongside results; stale-source cars are labeled and the dashboard falls back to the official country homepage.
- Final availability is still checked by the provider. Neither a link nor a notification constitutes a reservation.

### Vehicle model filter
- New include/exclude model name fields in **Configure → Vehicle preferences**.
- Semicolon-separated terms (for example `Crafter; Transporter`); exclusions take precedence.

### Trip cost breakdown
- **Configure → Trip cost assumptions**: enter petrol/diesel litres/100 km and NOK/litre; EV kWh/100 km and NOK/kWh.
- Defaults are blank/unknown (0), not guessed figures.
- Cars and phone notifications show estimated road toll and driving energy, plus a **partial subtotal** when components are known.
- Ferries, fees, provider billings and actual consumption remain excluded/uncertain.

### Radius-based station discovery
- **Configure → Search radius around stations** selects a verified station, plus 25, 50 or 100 km.
- Origin and destination areas may be configured independently; the same radius value applies.
- Straight-line GPS radius, not road travel distance. Existing manually selected stations remain eligible.

### Operational status and recent activity
- **Search status** diagnostic entity shows last attempted/successful scan, estimated next check, source errors, recent changes, successful/pending mobile notifications and the last push error.
- Bounded history of the 100 most recent changes, persisted locally across restarts.

## Install
1. Update the custom Freerider HA repository in HACS to **0.9.0**.
2. Restart Home Assistant.
3. Open **Settings → Devices & services → Freerider HA → Configure**, and choose the optional filters, radius, cost or notification pages.
4. Inspect the new **Search status** diagnostic entity under your watch device.

## Remaining limitations
This is an **independent community project, not endorsed by Hertz**. The API only supports Norwegian and Swedish source feeds. The provider's booking flow can still demand sign-in and reject a stale offer. Toll lookups for Norway have daily quotas and limited vehicle-weight information. No end-to-end user Home Assistant/mobile runtime trial is claimed by this release.

Report bugs at https://github.com/Wesc-9/Freerider_HA/issues .
