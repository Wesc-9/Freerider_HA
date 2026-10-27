"""Independently adjustable radius sliders from real selected stations."""
import unittest
from filters import Ride, ride_matches
from radius_settings import validate_radius_settings, radius_default

GPS = {
    "TRONDHEIM LUFTHAVN": {"lat": 63.457, "lon": 10.924},
    "STJØRDAL": {"lat": 63.468, "lon": 10.917},
    "OSLO LUFTHAVN": {"lat": 60.19, "lon": 11.1},
    "Equator": {"lat": 0, "lon": 0},
}


def offer(source="TRONDHEIM LUFTHAVN", target="OSLO LUFTHAVN",
          lat=63.457, lon=10.924, endlat=60.19, endlon=11.1):
    return Ride("NO", "1", source, target, "VW CRAFTER",
                "https://hertzfreerider.no/no-no/",
                pickup_lat=lat, pickup_lon=lon, return_lat=endlat,
                return_lon=endlon)


class RadiusSettingsTests(unittest.TestCase):
    def test_first_run_both_sides(self):
        settings = {"origin":["TRONDHEIM LUFTHAVN"],
            "destination":["OSLO LUFTHAVN"],
            "origin_radius_km":50, "destination_radius_km":25}
        got, error = validate_radius_settings(settings, GPS)
        self.assertIsNone(error)
        self.assertEqual(got["origin_radius_points"], [GPS["TRONDHEIM LUFTHAVN"]])
        self.assertEqual(got["destination_radius_points"], [GPS["OSLO LUFTHAVN"]])
        self.assertEqual(got["radius_km"], "0")
        self.assertTrue(ride_matches(offer(),{"countries":["NO"],**settings,**got}))

    def test_each_side_is_independent(self):
        settings = {"origin":["TRONDHEIM LUFTHAVN"],"destination":["OSLO LUFTHAVN"],
                    "origin_radius_km":25,"destination_radius_km":0}
        got,err=validate_radius_settings(settings,GPS)
        self.assertIsNone(err)
        self.assertEqual(got["destination_radius_points"],[])
        alternate=offer(source="STJØRDAL",lat=63.468,lon=10.917)
        self.assertTrue(ride_matches(alternate,{"countries":["NO"],**settings,**got}))
        far=offer(source="OSLO LUFTHAVN",target="OSLO LUFTHAVN",lat=60.19,lon=11.1)
        self.assertFalse(ride_matches(far,{"countries":["NO"],**settings,**got}))

    def test_multiple_locations_get_individual_centers(self):
        settings={"origin":["TRONDHEIM LUFTHAVN","STJØRDAL"],
                  "destination":["OSLO LUFTHAVN"],
                  "origin_radius_km":15,"destination_radius_km":0}
        got,err=validate_radius_settings(settings,GPS)
        self.assertIsNone(err)
        self.assertEqual(len(got["origin_radius_points"]),2)

    def test_zero_keeps_exact_place_selection(self):
        settings={"origin":["TRONDHEIM LUFTHAVN"],
                  "origin_radius_km":0,"destination_radius_km":0}
        got,err=validate_radius_settings(settings,GPS)
        self.assertIsNone(err)
        self.assertEqual(got["origin_radius_points"],[])
        self.assertFalse(ride_matches(offer(source="STJØRDAL"),{
            "countries":["NO"],**settings,**got,
        }))

    def test_unknown_location_rejected_if_radius_positive(self):
        got,err=validate_radius_settings({
            "origin":["CUSTOM PLACE"],"origin_radius_km":25},GPS)
        self.assertEqual(err,"radius_station_unavailable")
        self.assertEqual(got,{})

    def test_missing_origin_rejected_when_radius_active(self):
        _,err=validate_radius_settings({"origin_radius_km":10},GPS)
        self.assertEqual(err,"radius_center_required")

    def test_out_of_bounds(self):
        for bad in (-5,101,17,True, "nan"):
            with self.subTest(value=bad):
                _,err=validate_radius_settings({
                    "origin":["STJØRDAL"],"origin_radius_km":bad,
                },GPS)
                self.assertEqual(err,"radius_invalid")

    def test_legacy_default_converts_single_shared_radius(self):
        self.assertEqual(radius_default({"radius_km":25,
            "origin_radius_name":"TRONDHEIM LUFTHAVN"},"origin"),25)
        self.assertEqual(radius_default({"radius_km":25,
            "destination_radius_name":"OSLO LUFTHAVN"},"origin"),0)

    def test_zero_zero_coordinates_are_valid(self):
        got,err=validate_radius_settings({
            "origin":["Equator"],"origin_radius_km":5},GPS)
        self.assertIsNone(err)
        self.assertEqual(got["origin_radius_points"],[{"lat":0.0,"lon":0.0}])


if __name__=="__main__":
    unittest.main()
