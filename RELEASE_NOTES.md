# Freerider HA 0.5.0

Community test release for the unofficial **Freerider HA** Home Assistant integration.

## Changes
- Simplified station search: choose multiple departure places (e.g. Trondheim Sluppen and Værnes) and multiple destinations in the same profile.
- Search all combinations, or leave a column empty for any place.
- Dropdown station suggestions with custom typed locations.
- Optional dates now live in the route setup panel itself: blank = all dates, first date only = one day, both dates = a date range.
- Norwegian/English translations updated.
- Freerider HA name replaces Hertz branding in the product title. Internal technical domain is unchanged to preserve already configured integrations.
- Norway and Sweden public route feeds and optional Norwegian toll estimates are retained.

## Important
This project is **unofficial** and not affiliated with, sponsored by or endorsed by Hertz. Freerider cars, final pickup eligibility, toll fees and bookings are ultimately governed by the provider's current conditions.

**Known limitations:** Denmark source adapter not yet implemented; date ranges reflect published offer windows, not guaranteed pickup slots; on-device Home Assistant runtime verification and third-party API permission checks are still pending.

## Updating from HACS
Open **HACS → Freerider HA → Download/Update**, choose **0.5.0**, and restart Home Assistant. Existing saved profiles should remain intact. Manage origin/destination groups and dates from **Configure → Places and dates**.

https://github.com/Wesc-9/Freerider_HA/issues
