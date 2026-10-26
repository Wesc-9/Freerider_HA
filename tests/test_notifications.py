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
            available_start="2026-10-28", available_at="2026-10-28T11:30:00",
            latest_return_at="2026-10-30T17:00:00",
            offer_expires_at="2026-10-29T11:30:00",
            distance_km=346, drive_minutes=278,
        )

    def test_route_model_and_link(self):
        payload = notification_content(self.ride, "Trondheim to Bodø")
        self.assertIn("TRONDHEIM SLUPPEN → BODØ LUFTHAVN", payload["message"])
        self.assertIn("VOLVO XC40 AUT", payload["message"])
        self.assertIn("28.10 kl. 11:30", payload["message"])
        self.assertIn("346 km", payload["message"])
        self.assertIn("4 t 38 min", payload["message"])
        self.assertIn("Siste retur 30.10", payload["message"])
        self.assertEqual(payload["url"], "https://hertzfreerider.no/no-no/")

    def test_toll_cost_is_explicit_estimate(self):
        quote = {"amount_nok": 215.5, "ferry_count": 0}
        payload = notification_content(self.ride, "Trondheim", toll_estimate=quote)
        self.assertIn("216 kr", payload["message"])
        self.assertIn("uten AutoPASS-rabatt", payload["message"])
        self.assertIn("Drivstoff/lading kan forekomme", payload["message"])

    def test_toll_failure_never_shows_zero(self):
        payload = notification_content(self.ride, "Trondheim", toll_status="provider_error")
        self.assertIn("Estimat ikke tilgjengelig", payload["message"])
        self.assertNotIn("0 kr", payload["message"])

    def test_unsupported_cross_border_reports_no_estimate(self):
        payload = notification_content(self.ride, "Trondheim", language="en", toll_status="outside_norway")
        self.assertIn("Not calculated outside Norway", payload["message"])
        self.assertIn("approx. 4h 38m", payload["message"])

    def test_zero_from_provider_is_a_valid_quote(self):
        payload = notification_content(self.ride, "Trondheim", toll_estimate={"amount_nok": 0})
        self.assertIn("0 kr", payload["message"])

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
