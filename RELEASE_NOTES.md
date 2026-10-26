# Freerider HA 0.6.2

## Notifications now part of search registration

After choosing name and countries, the **From / To / Dates** screen also offers:

- **Notify me about new cars** — on/off switch (off by default).
- **Send notifications to** — select your registered Home Assistant Companion app phone, Home Assistant in-app notifications, or Off.

To receive new-car push alerts, choose your mobile device **and enable the toggle** before creating the saved search. The setup will warn if alerts are on but no recipient is chosen. There is no need for a separate notification configuration step.

For **existing searches**, open Freerider HA → Configure → **Places, dates and notifications**. Update the same settings there; previous route filters and entities are preserved. A corresponding New car alerts entity switch remains available on the search device for turning notifications on and off later.

The Test notification button can confirm delivery. New matching cars generate messages containing route, vehicle, date, offer ID and a link to the correct Freerider country's booking site. Due to the provider's session-based booking UI, the link is **not** yet a verified individual-car checkout link.

This is an unofficial community project, not affiliated with Hertz. Norway and Sweden data feeds supported; Denmark pending. Fuel/charging and toll costs may apply.

Install 0.6.2 from HACS and restart Home Assistant.
