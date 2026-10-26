"""Unit tests; use PYTHONPATH=custom_components/hertz_freerider."""

import unittest

from filters import Ride, filter_rides, ride_matches


RIDE = Ride(
    source_country="NO", source_id="no-1",
    origin="Trondheim lufthavn", destination="Bodø",
    vehicle="Volvo XC60", booking_url="https://example.invalid/1",
    available_start="2026-11-10", available_end="2026-11-15",
    transmission="automatic", vehicle_type="car", fuel="hybrid", seats=5,
)


class FilterTests(unittest.TestCase):
    def test_origin_and_destination_casefold(self):
        self.assertTrue(ride_matches(RIDE, {"countries":["NO"],"origin":"trondheim","destination":"bodo"}))
        self.assertFalse(ride_matches(RIDE, {"countries":["SE"]}))

    def test_either_direction(self):
        self.assertFalse(ride_matches(RIDE, {"countries":["NO"],"origin":"Bodø","destination":"Trondheim"}))
        self.assertTrue(ride_matches(RIDE, {"countries":["NO"],"origin":"Bodø","destination":"Trondheim","direction":"either"}))

    def test_date_overlap(self):
        self.assertTrue(ride_matches(RIDE, {"countries":["NO"],"date_mode":"single","date_start":"2026-11-12"}))
        self.assertFalse(ride_matches(RIDE, {"countries":["NO"],"date_mode":"single","date_start":"2026-11-16"}))
        self.assertTrue(ride_matches(RIDE, {"countries":["NO"],"date_mode":"range","date_start":"2026-11-01","date_end":"2026-11-10"}))
        self.assertFalse(ride_matches(RIDE, {"countries":["NO"],"date_mode":"range","date_start":"2026-11-16","date_end":"2026-11-25"}))

    def test_gearbox_vehicle_fuel_and_seats(self):
        self.assertTrue(ride_matches(RIDE, {"countries":["NO"],"transmission":"automatic","fuel":"hybrid","min_seats":5}))
        self.assertFalse(ride_matches(RIDE, {"countries":["NO"],"transmission":"manual"}))
        self.assertFalse(ride_matches(RIDE, {"countries":["NO"],"min_seats":6}))
        self.assertFalse(ride_matches(RIDE, {"countries":["NO"],"vehicle_type":"van"}))

    def test_unknown_data_never_fake_match(self):
        unknown = Ride("DK","dk-1","København","Aarhus","Unknown","https://example.invalid/2")
        self.assertFalse(ride_matches(unknown, {"countries":["DK"],"date_mode":"single","date_start":"2026-11-12"}))
        self.assertFalse(ride_matches(unknown, {"countries":["DK"],"transmission":"automatic"}))
        self.assertTrue(ride_matches(unknown, {"countries":["DK"]}))

    def test_multiple_countries(self):
        sweden = Ride("SE","se-1","Göteborg","Stockholm","Car","https://example.invalid/3")
        self.assertEqual([r.key for r in filter_rides([sweden, RIDE], {"countries":["NO","SE"]})],
                         ["NO:no-1", "SE:se-1"])


if __name__ == "__main__":
    unittest.main()
