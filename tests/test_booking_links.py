"""The provider's real booking-flow hash contract, not guessed listing URLs."""

import unittest
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlsplit

from booking_links import official_car_booking_url
from filters import Ride


def offer(**kwargs):
    fields={
        "source_country":"NO", "source_id":"67718",
        "origin":"TRONDHEIM SLUPPEN", "destination":"BODØ LUFTHAVN",
        "vehicle":"VOLVO XC40", "booking_url":"https://hertzfreerider.no/no-no/",
        "available_at":"2026-10-27T08:00:00",
        "offer_expires_at":"2026-10-30T18:00:00",
        "latest_return_at":"2026-11-01T18:00:00",
        "drive_minutes":420,
        "pickup_opening_hours":{
            str(day): {"openingTime":"1970-01-01T08:00:00", "closingTime":"1970-01-01T17:00:00"}
            for day in range(1,6)
        },
    }
    fields.update(kwargs)
    return Ride(**fields)


class ProviderDeepLinkTests(unittest.TestCase):
    def test_direct_to_exact_no_route_with_valid_date(self):
        url, direct=official_car_booking_url(offer(),now=datetime(2026,10,27,7,0))
        self.assertTrue(direct)
        parsed=urlsplit(url)
        self.assertEqual(parsed.scheme,"https")
        self.assertEqual(parsed.netloc,"hertzfreerider.no")
        self.assertEqual(parsed.path,"/booking-flow/no-no/")
        fragment=parse_qs(parsed.fragment)
        self.assertEqual(fragment["id"],["67718"])
        self.assertEqual(fragment["date"],["2026-10-27T08:00"])

    def test_swedish_localized_booking_flow(self):
        url,direct=official_car_booking_url(
            offer(source_country="SE"),now=datetime(2026,10,27,7,0)
        )
        self.assertTrue(direct)
        self.assertIn("hertzfreerider.se/booking-flow/sv-se/",url)

    def test_expired_offer_falls_back_safely(self):
        url,direct=official_car_booking_url(
            offer(),now=datetime(2026,11,5,9,0)
        )
        self.assertFalse(direct)
        self.assertEqual(url,"https://hertzfreerider.no/no-no/")

    def test_missing_pickup_info_does_not_fabricate_date(self):
        url,direct=official_car_booking_url(
            offer(drive_minutes=None),now=datetime(2026,10,27,7,0)
        )
        self.assertFalse(direct)
        self.assertEqual(url,"https://hertzfreerider.no/no-no/")

    def test_station_closed_until_next_day(self):
        url,direct=official_car_booking_url(
            offer(),now=datetime(2026,10,27,17,20)
        )
        self.assertTrue(direct)
        self.assertEqual(parse_qs(urlsplit(url).fragment)["date"],["2026-10-28T08:15"])

    def test_weekend_hours_skip_to_monday(self):
        url,direct=official_car_booking_url(
            offer(
                available_at="2026-10-30T20:00:00",
                offer_expires_at="2026-11-03T20:00:00",
                latest_return_at="2026-11-06T12:00:00",
            ),
            now=datetime(2026,10,30,20,0),
        )
        self.assertTrue(direct)
        self.assertEqual(parse_qs(urlsplit(url).fragment)["date"],["2026-11-02T08:15"])

    def test_unknown_offer_id_never_becomes_direct_link(self):
        url,direct=official_car_booking_url(
            offer(source_id="123/#evil"),now=datetime(2026,10,27,7,0)
        )
        self.assertFalse(direct)
        self.assertEqual(url,"https://hertzfreerider.no/no-no/")


if __name__=="__main__":
    unittest.main()
