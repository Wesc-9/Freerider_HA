"""GPS-only radius selection with same behavior in first-run and Options."""
import unittest
from radius_settings import parse_radius_selection


GPS = {
    "TRONDHEIM LUFTHAVN": {"lat": 63.457, "lon": 10.924},
    "OSLO LUFTHAVN": {"lat": 60.19, "lon": 11.1},
}


class RadiusSettingsTests(unittest.TestCase):
    def test_first_run_with_both_sides(self):
        values = {"radius_km": "50",
                  "origin_radius_name": "TRONDHEIM LUFTHAVN",
                  "destination_radius_name": "OSLO LUFTHAVN"}
        opts, err = parse_radius_selection(values, GPS)
        self.assertIsNone(err)
        self.assertEqual(opts["origin_radius_point"], GPS["TRONDHEIM LUFTHAVN"])
        self.assertEqual(opts["destination_radius_point"], GPS["OSLO LUFTHAVN"])
        self.assertEqual(opts["radius_km"], "50")

    def test_only_one_side_supported(self):
        opts, err = parse_radius_selection(
            {"radius_km": "25", "origin_radius_name": "TRONDHEIM LUFTHAVN"}, GPS,
        )
        self.assertIsNone(err)
        self.assertIsNone(opts["destination_radius_point"])

    def test_off_does_not_preserve_old_coordinates(self):
        opts, err = parse_radius_selection({"radius_km": "0",
                  "origin_radius_name": "TRONDHEIM LUFTHAVN"}, GPS)
        self.assertIsNone(err)
        self.assertEqual(opts["origin_radius_name"], "")
        self.assertIsNone(opts["origin_radius_point"])

    def test_no_unverified_station_gps(self):
        opts, err = parse_radius_selection(
            {"radius_km": "100", "origin_radius_name": "UNKNOWN"}, GPS,
        )
        self.assertEqual(err, "radius_station_unavailable")
        self.assertEqual(opts, {})

    def test_center_required_for_active_radius(self):
        _, err = parse_radius_selection({"radius_km": "25"}, GPS)
        self.assertEqual(err, "radius_center_required")

    def test_invalid_radius_rejected(self):
        _, err = parse_radius_selection({"radius_km": "123",
            "origin_radius_name": "TRONDHEIM LUFTHAVN"}, GPS)
        self.assertEqual(err, "radius_invalid")

    def test_zero_coordinates_are_valid(self):
        opts, err = parse_radius_selection({"radius_km": "25",
            "origin_radius_name": "Equator"}, {"Equator": {"lat": 0, "lon": 0}})
        self.assertIsNone(err)
        self.assertEqual(opts["origin_radius_point"], {"lat":0,"lon":0})


if __name__ == "__main__":
    unittest.main()
