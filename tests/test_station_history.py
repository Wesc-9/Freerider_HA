"""Station catalog regression tests: preserve historic places across updates."""

import unittest

from filters import Ride, known_station_names, merge_station_history


def ride(ride_id: str, origin: str, destination: str, country="NO"):
    return Ride(country, ride_id, origin, destination, "Car", "https://example.invalid")


class StationCatalogTests(unittest.TestCase):
    def test_new_locations_are_added_without_erasing_old(self):
        stored = {"NO": ["TRONDHEIM SLUPPEN", "BODØ LUFTHAVN"]}
        updated, added = merge_station_history(
            stored, "NO", [ride("1", "TRONDHEIM LUFTHAVN", "OSLO GARDERMOEN")]
        )
        self.assertEqual(added, 2)
        self.assertEqual(len(updated["NO"]), 4)
        self.assertIn("TRONDHEIM SLUPPEN", updated["NO"])
        self.assertIn("TRONDHEIM LUFTHAVN", updated["NO"])
        self.assertEqual(stored["NO"], ["TRONDHEIM SLUPPEN", "BODØ LUFTHAVN"])

    def test_empty_current_feed_keeps_all_historical_stations(self):
        previous = {"NO": ["Bergen", "Stavanger"]}
        result, added = merge_station_history(previous, "NO", [])
        self.assertEqual(added, 0)
        self.assertEqual(result, previous)

    def test_duplicate_and_accent_handling(self):
        previous = {"NO": ["Bodø lufthavn"]}
        result, added = merge_station_history(
            previous, "NO", [ride("1", "BODO LUFTHAVN", "Bergen")]
        )
        self.assertEqual(added, 1)
        self.assertEqual(len(result["NO"]), 2)
        self.assertIn("Bodø lufthavn", result["NO"])

    def test_country_source_separation_with_global_dedup(self):
        history = {"NO": ["Bergen", "Oslo"], "SE": ["Göteborg", "Oslo"]}
        self.assertEqual(len(known_station_names(history, ["NO", "SE"])), 3)
        self.assertEqual(known_station_names(history, ["SE"]), ["Göteborg", "Oslo"])

    def test_repeated_scan_without_new_names(self):
        first, added1 = merge_station_history({}, "NO", [ride("1", "Tromsø", "Bodø")])
        second, added2 = merge_station_history(first, "NO", [ride("2", "Tromsø", "Bodø")])
        self.assertEqual(added1, 2)
        self.assertEqual(added2, 0)
        self.assertEqual(first, second)

    def test_unverified_country_not_added(self):
        original = {"NO": ["Oslo"]}
        result, added = merge_station_history(original, "ZZ", [ride("1", "A", "B")])
        self.assertEqual(added, 0)
        self.assertEqual(result, original)


if __name__ == "__main__":
    unittest.main()
