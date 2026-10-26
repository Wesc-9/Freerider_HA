# Changelog

## 0.5.0 (2026-10-26) — multiple locations, dates in one screen and neutral branding

- Renamed the **displayed** integration to **Freerider HA** throughout Home Assistant, HACS and the README (the internal domain remains `hertz_freerider` for backwards compatibility).
- Choose multiple departure **and** arrival stations in the same searchable comboboxes; any departure is matched against any arrival.
- Supports typed station names even when missing from current Hertz station suggestions, plus a Værnes/Trondheim Airport alias.
- Added optional travel dates directly to the route step: no dates = any, first date alone = one day, first/last = a date range.
- Existing single-station search profiles continue to work; update them through Configure.
- Updated Norwegian and English UI copy and independent-service disclaimers.
- Release tag `0.5.0` without a leading `v` for straightforward HACS version identification.


## v0.4.0 (2026-10-26) — community test release
- New native guided setup for countries, locations and dates.
- Station suggestions with optional free-text search.
- Norwegian and English translations.
- Advanced filtering and alert preferences moved to configuration submenus.
- Working public route feeds for Norway and Sweden.
- Manual toll estimation for Norwegian routes and clear extra-cost notices.
- Independent project disclaimer and HACS install instructions.
- GitHub release and HACS version publishing automation.

### Known gaps
- Denmark feed unavailable.
- Exact booking times and Home Assistant runtime behavior require broader field testing.
- Full HACS publish validation requires repository Topics metadata.
