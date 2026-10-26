"""Check actual Home Assistant service payloads without sending network alerts."""

import unittest

from notifications import (
    async_send_notification, notification_content, TARGET_OFF, TARGET_PERSISTENT,
)
from filters import Ride


class Services:
    def __init__(self):
        self.calls = []

    def has_service(self, domain, name):
        return (domain, name) in (
            ("notify", "mobile_app_iphone"),
            ("persistent_notification", "create"),
        )

    async def async_call(self, domain, name, data, blocking):
        self.calls.append((domain, name, data, blocking))


class HA:
    def __init__(self):
        self.services = Services()


class NotificationDispatchTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.hass = HA()
        ride = Ride(
            "SE", "22", "STOCKHOLM", "GÖTEBORG", "VOLVO XC40 AUT",
            "https://hertzfreerider.se/sv-se/",
        )
        self.payload = notification_content(ride, "My Watch", language="en")

    async def test_push_contains_click_through(self):
        success = await async_send_notification(
            self.hass, "mobile_app:mobile_app_iphone", self.payload,
        )
        self.assertTrue(success)
        domain, name, data, blocking = self.hass.services.calls[0]
        self.assertEqual((domain, name), ("notify", "mobile_app_iphone"))
        self.assertEqual(data["data"]["clickAction"], "https://hertzfreerider.se/sv-se/")
        self.assertEqual(data["data"]["url"], data["data"]["clickAction"])
        self.assertIn("STOCKHOLM", data["message"])
        self.assertTrue(blocking)

    async def test_off_does_not_send(self):
        self.assertFalse(await async_send_notification(self.hass, TARGET_OFF, self.payload))
        self.assertEqual(self.hass.services.calls, [])

    async def test_unavailable_phone_does_not_send_elsewhere(self):
        self.assertFalse(await async_send_notification(
            self.hass, "mobile_app:mobile_app_missing", self.payload,
        ))
        self.assertEqual(self.hass.services.calls, [])

    async def test_ha_in_app_message_has_clickable_url(self):
        self.assertTrue(await async_send_notification(
            self.hass, TARGET_PERSISTENT, self.payload,
        ))
        domain, service, data, _ = self.hass.services.calls[0]
        self.assertEqual((domain, service), ("persistent_notification", "create"))
        self.assertIn("[Åpne Freerider](https://hertzfreerider.se/sv-se/)", data["message"])


if __name__ == "__main__":
    unittest.main()
