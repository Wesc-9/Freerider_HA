"""Station suggestion normalization tests."""

import unittest
from filters import Ride, station_candidates

class StationTests(unittest.TestCase):
    def test_station_search_suggestions_include_all_endpoints(self):
        rides = [
            Ride("NO", "1", "TRONDHEIM", "Bodø lufthavn", "Car", "https://example.org"),
            Ride("SE", "2", "BODO LUFTHAVN", "Göteborg", "Car", "https://example.org"),
            Ride("SE", "3", "Trondheim", "Stockholm", "Car", "https://example.org"),
        ]
        suggestions = station_candidates(rides)
        self.assertEqual(len(suggestions), 4)
        self.assertIn("Bodø lufthavn", suggestions)
        self.assertIn("Göteborg", suggestions)
        self.assertIn("TRONDHEIM", suggestions)

    def test_empty_input(self):
        self.assertEqual(station_candidates([]), [])

if __name__ == "__main__":
    unittest.main()
