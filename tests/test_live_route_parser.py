"""Tests for the verified public NO/SE grouped-route response shape.

These fixtures contain no user personal data and require no live website access.
"""
import unittest
from filters import parse_transport_routes, ride_matches


class PublicFeedParserTest(unittest.TestCase):
    def test_route_group_and_fields(self):
        payload = [{
            "pickupLocationName": "TRONDHEIM SLUPPEN",
            "returnLocationName": "BODØ LUFTHAVN",
            "routes": [{
                "id": 67718,
                "transportOfferId": 45632,
                "pickupLocation": {"name": "TRONDHEIM SLUPPEN", "country": "no"},
                "returnLocation": {"name": "BODØ LUFTHAVN", "country": "no"},
                "availableAt": "2026-10-26T11:00:00",
                "expireTime": "2026-11-02T17:00:00",
                "latestReturn": "2026-11-03T12:00:00",
                "carModel": "VOLVO XC40 AUT ELECTRIC",
            }],
        }]
        rides = parse_transport_routes(payload, "NO", "https://hertzfreerider.no/no-no/")
        self.assertEqual(len(rides), 1)
        ride = rides[0]
        self.assertEqual(ride.key, "NO:67718")
        self.assertEqual(ride.origin, "TRONDHEIM SLUPPEN")
        self.assertEqual(ride.available_start, "2026-10-26")
        self.assertEqual(ride.available_end, "2026-11-02")
        self.assertEqual(ride.latest_return_at, "2026-11-03T12:00:00")
        self.assertEqual(ride.transmission, "automatic")
        self.assertEqual(ride.fuel, "electric")
        self.assertTrue(ride_matches(ride, {
            "countries": ["NO"], "origin": "trondheim", "destination": "bodo",
            "transmission": "automatic", "date_mode": "single",
            "date_start": "2026-10-29",
        }))

    def test_empty_valid_result_and_malformed_feed(self):
        self.assertEqual(parse_transport_routes([], "SE", "https://hertzfreerider.se/"), [])
        with self.assertRaises(ValueError):
            parse_transport_routes({"routes": []}, "SE", "https://hertzfreerider.se/")

    def test_empty_invalid_elements_skipped(self):
        result = parse_transport_routes(
            [{"routes": [None, {"id": 123, "pickupLocation": None, "returnLocation": None}]}],
            "NO", "https://hertzfreerider.no/",
        )
        self.assertEqual(result, [])

    def test_cross_border_route(self):
        result = parse_transport_routes(
            [{"routes": [{
                "id": 67623,
                "pickupLocation": {"name": "EVENES LUFTHAVN", "country": "no"},
                "returnLocation": {"name": "Kiruna AP", "country": "se"},
                "carModel": "VOLVO XC40 B3 FWD AUT",
                "availableAt": "2026-10-22T06:45:00",
                "expireTime": "2026-10-29T20:29:00",
                "latestReturn": "2026-10-30T22:45:00",
            }]}],
            "SE", "https://hertzfreerider.se/sv-se/",
        )
        self.assertEqual(result[0].source_country, "SE")
        self.assertEqual(result[0].origin, "EVENES LUFTHAVN")
        self.assertEqual(result[0].destination, "Kiruna AP")
        self.assertEqual(result[0].transmission, "automatic")


if __name__ == "__main__":
    unittest.main()
