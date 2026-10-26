"""Unit checks: only known Norwegian small-car routes get toll estimates."""

import unittest

from filters import Ride
from quote_rules import quote_eligibility


def car(**changes):
    values = dict(
        source_country="NO", source_id="1",
        origin="Trondheim", destination="Bodø",
        vehicle="VOLVO", booking_url="https://hertzfreerider.no/",
        pickup_country="no", return_country="no",
        pickup_lat=63.4, pickup_lon=10.4,
        return_lat=67.2, return_lon=14.4,
    )
    values.update(changes)
    return Ride(**values)


class TollRuleTests(unittest.TestCase):
    def test_normal_norwegian_route(self):
        self.assertEqual(quote_eligibility(car()), "ok")

    def test_both_ends_must_be_in_norway(self):
        self.assertEqual(
            quote_eligibility(car(return_country="se")), "outside_norway",
        )

    def test_vans_and_minibuses_do_not_get_small_vehicle_price(self):
        self.assertEqual(
            quote_eligibility(car(vehicle_type="van")),
            "unknown_heavy_vehicle_rate",
        )
        self.assertEqual(
            quote_eligibility(car(vehicle_type="minibus")),
            "unknown_heavy_vehicle_rate",
        )

    def test_missing_gps_means_no_quote(self):
        self.assertEqual(
            quote_eligibility(car(return_lat=None)),
            "missing_coordinates",
        )


if __name__ == "__main__":
    unittest.main()
