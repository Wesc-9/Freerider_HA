"""No external API calls; validates conservative Norwegian toll results."""

import unittest
from toll_parser import parse_toll_response


PAYLOAD = {
    "_billing": {
        "source": "svv-ruteplan-v3",
        "refined": True,
        "routes": [{
            "routeId": "test-route",
            "tollSmall": 40,
            "tollSmallNoDiscount": 50,
            "tollSmallEvNoDiscount": 26,
            "tollSmallEv": 20.8,
            "tollCount": 1,
            "distance": 43078,
            "durationMin": 34.65,
            "ferryCount": 1,
            "chargedStations": [
                {"name": "E18 Bygdøylokket"},
                {"name": "E18 Maritim", "_coveredByTimesregel": True},
            ],
        }],
    },
}


class TollTests(unittest.TestCase):
    def test_uses_full_rental_rate_not_autopass_discount(self):
        result = parse_toll_response(PAYLOAD, electric=False)
        self.assertEqual(result["amount_nok"], 50)
        self.assertEqual(result["toll_count"], 1)
        self.assertEqual(result["distance_km"], 43.1)
        self.assertEqual(result["duration_min"], 34.6)
        self.assertEqual(len(result["toll_stations"]), 2)
        self.assertTrue(result["toll_stations"][1]["covered_by_hour_rule"])
        self.assertFalse(result["ferry_included"])

    def test_obstruction_true_on_correct_recommended_route(self):
        payload = {
            "routes": [
                {"routeId":"another","isObstructed":False},
                {"routeId":"test-route","isObstructed":True,
                 "obstructingFeatures":[{"type":"Feature"},{"type":"Feature"}]},
            ],
            "_billing":PAYLOAD["_billing"],
        }
        result=parse_toll_response(payload,electric=False)
        self.assertIs(result["road_obstructed"],True)
        self.assertEqual(result["road_obstruction_count"],2)
        self.assertEqual(result["amount_nok"],50)

    def test_flag_false_only_when_explicitly_returned(self):
        payload={
            "routes":[{"routeId":"test-route","isObstructed":False}],
            "_billing":PAYLOAD["_billing"],
        }
        self.assertIs(parse_toll_response(payload,electric=False)["road_obstructed"],False)

    def test_unknown_traffic_is_never_called_clear(self):
        payload={"_billing":PAYLOAD["_billing"]}
        self.assertIsNone(parse_toll_response(payload,electric=False)["road_obstructed"])
        payload={
            "routes":[{"routeId":"test-route","isObstructed":"false"}],
            "_billing":PAYLOAD["_billing"],
        }
        self.assertIsNone(parse_toll_response(payload,electric=False)["road_obstructed"])

    def test_no_wrong_route_obstruction_flag(self):
        payload={
            "routes":[{"routeId":"different-route","isObstructed":True}],
            "_billing":PAYLOAD["_billing"],
        }
        self.assertIsNone(parse_toll_response(payload,electric=False)["road_obstructed"])

    def test_electric_no_discount(self):
        result = parse_toll_response(PAYLOAD, electric=True)
        self.assertEqual(result["amount_nok"], 26)

    def test_unknown_amount_not_reported_as_zero(self):
        with self.assertRaises(ValueError):
            parse_toll_response({"_billing": {"routes": [{}]}}, electric=False)

    def test_zero_is_valid_when_provider_reports_it(self):
        self.assertEqual(
            parse_toll_response({"_billing": {"routes": [{"tollSmallNoDiscount": 0}]}},
                                electric=False)["amount_nok"], 0,
        )

    def test_rejects_missing_billing(self):
        with self.assertRaises(ValueError):
            parse_toll_response({"routes": []}, electric=False)


if __name__ == "__main__":
    unittest.main()
