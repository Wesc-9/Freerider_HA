"""Model include/exclude, safe radius and inventory change behaviour."""
import unittest
from filters import Ride, ride_matches
from search_enhancements import distance_km, classify_offers
from trip_costs import cost_breakdown


def ride(key="1", **kwargs):
    d=dict(source_country="NO",source_id=key,origin="Trondheim lufthavn",
           destination="Bodø",vehicle="VW Crafter 14M3 AUT",
           booking_url="https://hertzfreerider.no/no-no/",
           pickup_lat=63.458,pickup_lon=10.924,
           return_lat=67.280,return_lon=14.405,
           available_at="2026-10-26T10:00:00",
           offer_expires_at="2026-10-27T10:00:00",
           latest_return_at="2026-10-28T19:00:00")
    d.update(kwargs)
    return Ride(**d)


class SearchTests(unittest.TestCase):
    def test_model_include_exclude_with_accents(self):
        r=ride()
        self.assertTrue(ride_matches(r,{"countries":["NO"],"model_include":"Volvo; Crafter"}))
        self.assertFalse(ride_matches(r,{"countries":["NO"],"model_exclude":"Crafter"}))
        self.assertTrue(ride_matches(r,{"countries":["NO"],"model_include":"Volvo; Crafter", "model_exclude":"Transporter"}))
        self.assertFalse(ride_matches(r,{"countries":["NO"],"model_include":"Volvo"}))

    def test_radius_from_airport_and_unknown_coordinate(self):
        opts={"countries":["NO"],"radius_km":25,
              "origin_radius_name":"Trondheim lufthavn",
              "origin_radius_point":{"lat":63.458,"lon":10.925}}
        self.assertTrue(ride_matches(ride(),opts))
        self.assertFalse(ride_matches(ride(pickup_lat=None),opts))
        opts["radius_km"]=1
        opts["origin_radius_point"]={"lat":59.91,"lon":10.75}
        self.assertFalse(ride_matches(ride(),opts))

    def test_origin_text_or_radius_but_destination_must_match(self):
        opts={"countries":["NO"],"origin":["Oslo"],"destination":["Bodø"],
              "radius_km":25,"origin_radius_name":"Værnes",
              "origin_radius_point":{"lat":63.458,"lon":10.925}}
        self.assertTrue(ride_matches(ride(),opts))
        opts["destination"]=["Bergen"]
        self.assertFalse(ride_matches(ride(),opts))

    def test_invalid_coordinate_does_not_match(self):
        self.assertIsNone(distance_km(91,10,63,10))
        self.assertIsNone(distance_km(None,10,63,10))

    def test_initial_alerts_opt_in(self):
        rs=[ride()]
        a,ev,state=classify_offers(None,rs,{"NO"},None)
        self.assertEqual(a,[])
        self.assertEqual(ev,[])
        a,_,_=classify_offers(None,rs,{"NO"},None,True)
        self.assertEqual(a[0][1],"existing")

    def test_updated_dates_remove_and_partial_failure(self):
        one=ride()
        _,_,prev=classify_offers(None,[one],{"NO"},None)
        changed=ride(available_at="2026-10-26T12:00:00")
        alerts,events,after=classify_offers(prev,[changed],{"NO"},set())
        self.assertEqual([(r.key,kind) for r,kind in alerts],[("NO:1","updated")])
        self.assertEqual(events[0]["kind"],"updated")
        _,events,after=classify_offers(prev,[],{"SE"},set())
        self.assertEqual(events,[])
        self.assertIn(one.key,after)
        _,events,after=classify_offers(prev,[],{"NO"},set())
        self.assertEqual(events[0]["kind"],"removed")
        self.assertNotIn(one.key,after)

    def test_known_partial_costs_and_unknown_not_zero(self):
        r=ride(distance_km=200,fuel="diesel")
        result=cost_breakdown(r,{"amount_nok":145,"ferry_count":1},{
           "fuel_l_100km":8,"fuel_price_nok_l":22
        })
        self.assertEqual(result["energy_nok"],352)
        self.assertEqual(result["known_subtotal_nok"],497)
        self.assertTrue(result["has_unknown_components"])
        self.assertIsNone(cost_breakdown(r,None,{})["known_subtotal_nok"])


if __name__=="__main__":
    unittest.main()
