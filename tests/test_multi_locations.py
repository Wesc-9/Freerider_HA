"""Multi-place search tests, including legacy config and airport aliases."""

import unittest
from filters import Ride, filter_rides, place_values, ride_matches, station_matches

ROUTES = [
    Ride("NO","1","TRONDHEIM SLUPPEN","BODØ LUFTHAVN","Car","https://example.invalid/a"),
    Ride("NO","2","TRONDHEIM LUFTHAVN","OSLO GARDERMOEN","Car","https://example.invalid/b"),
    Ride("NO","3","BERGEN","BODØ LUFTHAVN","Car","https://example.invalid/c"),
    Ride("NO","4","TRONDHEIM LUFTHAVN","STAVANGER","Car","https://example.invalid/d"),
]

class MultiLocationTest(unittest.TestCase):
    def test_multiple_origins_and_destinations_are_cross_combined(self):
        config={
            "countries":["NO"],
            "origin":["Trondheim sluppen","Værnes"],
            "destination":["Bodø","Oslo"],
        }
        self.assertCountEqual(
            [r.key for r in filter_rides(ROUTES,config)],
            ["NO:1","NO:2"],
        )

    def test_legacy_string_still_works(self):
        self.assertTrue(ride_matches(ROUTES[0], {
            "countries":["NO"],"origin":"Trondheim","destination":"Bodø",
        }))

    def test_blank_column_means_anywhere(self):
        self.assertEqual(len(filter_rides(ROUTES,{
            "countries":["NO"],"origin":[],"destination":["Bodø"],
        })),2)

    def test_both_directions(self):
        backwards=Ride("NO","5","BODØ LUFTHAVN","TRONDHEIM SLUPPEN","Car","https://example.invalid/e")
        query={"countries":["NO"],"origin":["Trondheim sluppen","Værnes"],"destination":["Bodø","Oslo"]}
        self.assertFalse(ride_matches(backwards,query))
        self.assertTrue(ride_matches(backwards,{**query,"direction":"either"}))

    def test_deduplicate_case_and_accents(self):
        self.assertEqual(place_values([" Værnes ","Vaernes","TRONDHEIM",""]),["Værnes","TRONDHEIM"])
        self.assertTrue(station_matches("Værnes","TRONDHEIM LUFTHAVN"))

    def test_comma_in_one_station_name_remains_intact(self):
        self.assertEqual(place_values("Airport, Terminal 1"),["Airport, Terminal 1"])

    def test_unavailable_route_not_implicitly_matched(self):
        self.assertFalse(ride_matches(ROUTES[2],{
            "countries":["NO"],"origin":["Værnes","Trondheim sluppen"],"destination":["Bodø","Oslo"],
        }))

if __name__=="__main__":
    unittest.main()
