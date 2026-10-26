"""Unit tests for safe, clickable Freerider notification content."""

import unittest

from filters import Ride
from notifications import (
    TARGET_OFF, TARGET_PERSISTENT, notification_content,
    notification_targets, official_url,
)


class FakeServices:
    def async_services(self):
        return {"notify": {
            "mobile_app_iphone": object(),
            "mobile_app_android_phone": object(),
            "notify": object(),
        }}


class FakeHA:
    services = FakeServices()


class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.ride = Ride(
            "NO", "123", "TRONDHEIM SLUPPEN", "BODØ LUFTHAVN",
            "VOLVO XC40 AUT", "https://hertzfreerider.no/no-no/",
            available_start="2026-10-28",
        )

    def test_route_model_and_link(self):
        payload = notification_content(self.ride, "Trondheim to Bodø")
        self.assertIn("TRONDHEIM SLUPPEN → BODØ LUFTHAVN", payload["message"])
        self.assertIn("VOLVO XC40 AUT", payload["message"])
        self.assertIn("2026-10-28", payload["message"])
        self.assertEqual(payload["url"], "https://hertzfreerider.no/no-no/")

    def test_reject_external_booking_link(self):
        self.assertEqual(
            official_url("https://example.invalid/malicious", "SE"),
            "https://hertzfreerider.se/sv-se/",
        )
        self.assertEqual(official_url("http://hertzfreerider.no/", "NO"),
                         "https://hertzfreerider.no/no-no/")

    def test_options_list_real_mobile_app_services(self):
        names = dict(notification_targets(FakeHA()))
        self.assertIn("mobile_app:mobile_app_iphone", names)
        self.assertIn("mobile_app:mobile_app_android_phone", names)
        self.assertNotIn("mobile_app:notify", names)
        self.assertIn(TARGET_OFF, names)
        self.assertIn(TARGET_PERSISTENT, names)

    def test_selected_target_stays_in_list(self):
        names = dict(notification_targets(FakeHA(), "mobile_app:mobile_app_retired"))
        self.assertIn("mobile_app:mobile_app_retired", names)


if __name__ == "__main__":
    unittest.main()
