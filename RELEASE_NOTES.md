# Freerider HA 0.10.1

## A simpler first-time setup

Choose origin and destination locations on the usual second screen. Each is immediately followed by an independent **0–100 km radius slider** (5 km steps). 0 km means only selected locations. Radius includes actual provider-listed GPS stations within straight-line distance of each selected reference. No coordinates are fabricated; entering an unknown custom place with a nonzero radius shows a validation message.

**All dates — notify me whenever a matching car appears** is turned on by default. Any previous date filter is cleared when selected. Start/end date previews are visibly disabled in that form.

To choose a date range, turn All dates off and continue. The setup asks for the **first date**, then advances to the **last date** step; last date is optional for a single-day search. A picker-to-picker auto-focus without submitting the step is not supported by the installed HA frontend, so each step requires its standard Next button.

## Disable and notifications
- Home Assistant's native **Disable** flow fixed by leaving lifecycle callbacks to HA instead of mistakenly calling config-entry unload twice.
- A separate **Search active** switch under each watch stops the watch's polling and notifications while preserving its entire configuration.
- The existing **New car alerts** switch continues to mute alerts only.
- Phone messages show the provider's exact car name (such as VW CRAFTER 14M3 4MOTION TDI VA) **without a preceding emoji**, in both languages.

## After updating
Update to **0.10.1** in HACS, restart Home Assistant, add a test search and inspect its radius sliders and All dates switch. For an existing search select Freerider HA → Configure → Places, dates and notifications. Use the device's Search active switch to pause only that search, or native Disable to stop the config entry.

### Validation and limitations
Automated Python tests, JavaScript tests and Home Assistant hassfest verify the implementation; a successful native Disable and date-picker UX in the user's real Home Assistant instance must still be confirmed. HACS publication validation may still be blocked by missing GitHub repository Topics. This is an unofficial project not affiliated with Hertz; permission to poll a public endpoint at a given frequency is not established. Leiebilretur/other providers are deliberately not mixed in without verifying supported data access and terms.
