# Freerider HA 0.5.1

Community test release for the unofficial Freerider HA integration.

## What's new
- **Smart station history:** every station seen in an actual Norwegian or Swedish listing feed is saved inside your Home Assistant installation.
- **Places won't disappear:** even if a car is gone later, the previously discovered station remains available as a suggestion.
- **New towns automatically appear:** the existing background route checks update the catalog whenever a new source station is published.
- The catalog is shared across all Freerider search profiles on that Home Assistant instance, and survives restarts.
- Already selected chips are removed from the initial suggestion choices when opening the search settings again.
- Multiple departure/arrival stations, free-text entries, and date/date-range selection continue to work.

## UI limitation
Home Assistant's built-in multi-select and date picker control live dropdown updates and calendar closing. This integration can filter the suggestions when a form opens, but **cannot guarantee immediate removal from an already-open dropdown or automatically force-close the date calendar** through the native config flow. Both require frontend-level functionality.

## Notes
Norway and Sweden have working read-only route data sources. Denmark remains pending. Date filters match advertised offer periods, not necessarily guaranteed bookable pickup times. This is an unofficial project, not affiliated with or endorsed by Hertz.

## Updating
Update Freerider HA to **0.5.1** in HACS and restart Home Assistant. Existing search profiles and settings are retained. The historical station database starts collecting locally when 0.5.1 runs.
