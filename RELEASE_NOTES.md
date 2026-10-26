# Freerider HA 0.6.1

This update makes new-car alerts easy to configure and manage directly in Home Assistant.

### Notifications
1. Open **Settings → Devices & services → Freerider HA → Configure**.
2. Choose **Automatic checks and notifications**.
3. Select **Send notifications to** and choose your registered phone (Home Assistant Companion app), or choose **Home Assistant notifications** for in-app alerts.
4. Save. The **New car alerts** switch is enabled automatically when you select a phone. Toggle it off/on any time, without deleting the recipient.
5. Find the search device in the integration and press **Test notification**. You should receive a clearly marked test alert.
6. New matching cars trigger push notifications after the initial baseline. The message contains the car model, route, offer ID, earliest listed date and link to the official provider site.

**Booking links:** The Norwegian and Swedish public route feeds do not provide a confirmed deep link to a single specific car. Tapping the alert opens the official Freerider website for the car's country, where you can find and reserve the listing. The alert includes the route/vehicle information to identify it. No booking is created automatically.

### Other improvements
- All sensor, button and switch entities are grouped as a Home Assistant device for each search.
- Failed phone delivery is retried on later successful route checks while the offer still appears.
- A maximum of eight alert attempts per scan, to reduce noise.
- Existing search profiles and event-trigger automations remain compatible.

**Note:** This is an unofficial community project, not endorsed or affiliated with Hertz. No live Home Assistant phone test is claimed. Denmark feed remains unavailable, and fuel/charging/tolls may apply.

Update to `0.6.1` in HACS, restart Home Assistant and configure your notification destination.
