"""Screen actual provider timings and rankings without external APIs."""
import unittest
from datetime import datetime
from filters import Ride
from trip_planner import journey_feasibility, sort_offers, quiet_now, is_urgent, km_airline

def ride(id, minutes=120, km=200, deadline="2026-10-28T18:00:00", expires="2026-10-28T17:00:00"):
    return Ride("NO",str(id),"TRONDHEIM","OSLO","VW CRAFTER",
                "https://hertzfreerider.no/no-no/",drive_minutes=minutes,
                distance_km=km,available_at="2026-10-27T08:00:00",
                latest_return_at=deadline,offer_expires_at=expires,
                pickup_lat=63.4,pickup_lon=10.4)

class PlannerTests(unittest.TestCase):
    def test_proposed_margin_includes_pickup_buffer(self):
        x=journey_feasibility(ride(1),datetime(2026,10,27,9))
        self.assertEqual(x["margin_minutes"], (24+9)*60-150)
        self.assertEqual(x["status"],"comfortable")

    def test_impossible_deadline(self):
        x=journey_feasibility(ride(1,minutes=999,deadline="2026-10-27T10:00:00"),datetime(2026,10,27,9))
        self.assertEqual(x["status"],"insufficient")

    def test_expired_offer(self):
        x=journey_feasibility(ride(1),datetime(2026,10,29,9))
        self.assertEqual(x["status"],"expired")

    def test_missing_duration_not_guessed(self):
        self.assertEqual(journey_feasibility(ride(1, minutes=None),datetime(2026,10,27,9))["status"],"unknown")

    def test_sort_missing_last(self):
        arr=[ride(1,300,500),ride(2,60,100),ride(3,None,None)]
        self.assertEqual([x.key for x in sort_offers(arr,"short_drive")],["NO:2","NO:1","NO:3"])
        self.assertEqual([x.key for x in sort_offers(arr,"short_route")],["NO:2","NO:1","NO:3"])

    def test_cheapest_known_not_unknown_as_free(self):
        arr=[ride(1),ride(2),ride(3)]
        costs={"NO:1":{"known_subtotal_nok":550},"NO:2":{"known_subtotal_nok":100}}
        self.assertEqual([x.key for x in sort_offers(arr,"low_cost",costs)],["NO:2","NO:1","NO:3"])

    def test_quiet_period_crosses_midnight(self):
        self.assertTrue(quiet_now("22:30","07:00",datetime(2026,10,27,23)))
        self.assertTrue(quiet_now("22:30","07:00",datetime(2026,10,27,6)))
        self.assertFalse(quiet_now("22:30","07:00",datetime(2026,10,27,12)))

    def test_urgent_only_for_confirmed_expiry(self):
        self.assertTrue(is_urgent(ride(1,expires="2026-10-27T11:00:00"),datetime(2026,10,27,9)))
        self.assertFalse(is_urgent(ride(1,expires=None),datetime(2026,10,27,9)))

    def test_airline_distance(self):
        self.assertEqual(km_airline(63.4,10.4,63.4,10.4),0)

if __name__=="__main__":
    unittest.main()
