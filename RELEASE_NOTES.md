# Freerider HA 0.10.3 — key-based toll estimates, compact cards and safe route warnings

### Configure your free API key
1. Open **[BompengeAppen's free registration portal](https://bompengeappen.no/api-portal)** and sign up with an email address. Free keys allow 500 calls/day according to the provider.
2. When creating a new Freerider watch, enter the key in the masked **BompengeAppen API key** field on the first screen. The signup link is shown directly underneath.
3. For an existing watch, go to **Freerider HA → Configure → Toll, API key and travel expenses**. Paste the key and save. Blank keeps an already-saved key.
4. Update to **0.10.3** in HACS and restart Home Assistant.

You can still watch Freerider car listings without a BompengeAppen key. To fetch **toll quotes and optional route warnings**, a key is required. Only Home Assistant's backend sends it to the provider, via HTTPS `Authorization: Bearer`. The key is masked in the form and excluded from sensor attributes and push payloads.

### Estimates and road conditions
- The Freerider dashboard card is denser and shows provider distance/drive time; for eligible Norwegian passenger-car listings, tap **Calculate toll and road status**. The response contains the planned-route toll amount, duration, distance and an obstruction flag when supplied.
- Vehicle models like VW Crafter remain shown exactly as Freerider published them. If the permitted total weight/toll class is unknown, we do not apply an unverified passenger-car rate.
- A route flag from BompengeAppen is **not a complete live national road closure feed**. Unknown means not checked, and even a clear route response does not guarantee open roads later. No separate API access to Statens vegvesen is needed.

### Compact setup layout
- Field labels are shorter and the advanced direction filter moved under Configure.
- Home Assistant's native config form continues to stack the From/To date fields vertically. We cannot put them on one horizontal line without creating an entirely separate frontend. Both are active on the same screen when dates are relevant.

Regression tests and CI validate the integration, but the actual new form layout and phone display still require testing in your Home Assistant app. The HACS publish validator may continue to flag the repository's missing GitHub Topics.

Unofficial community project; not affiliated with Hertz or BompengeAppen.
