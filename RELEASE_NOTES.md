# Freerider HA 0.10.5 — one BompengeAppen API key for all searches

- On the **first-ever Freerider setup screen**, enter one optional BompengeAppen key: [get a free key](https://bompengeappen.no/api-portal).
- Later searches do not ask for another key. No API fields appear in a search's device cost settings; the shared key is available automatically for eligible Norwegian routes.
- To change or remove it later, open the first-created Freerider search in **Settings → Devices & services → Freerider HA → Configure → Shared API settings (all searches)**. Blank keeps your saved key; check the clear option to remove it for all searches.
- **Existing installations**: stored per-search keys are migrated automatically into private global Home Assistant storage when entries load, then removed from individual entries. Search names, dates, filters and alerts stay unchanged.
- All toll lookups still require a key and are requested through Home Assistant's backend, never the browser. Cost estimates are not guaranteed prices. No separate Statens vegvesen API is used.
- **Install**: update to 0.10.5 via HACS, restart Home Assistant and check an eligible Norwegian route's toll calculation. This project's automated checks do not replace in-app device testing.

Unofficial community project; not affiliated with Hertz or BompengeAppen.
