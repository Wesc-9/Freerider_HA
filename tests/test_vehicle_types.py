"""Regression tests for vehicle classification and safe toll quoting."""

import unittest
from filters import Ride, parse_transport_routes
from quote_rules import quote_eligibility


def example(model):
    return parse_transport_routes([{
        "routes": [{
            "id": 67865,
            "pickupLocation": {"name": "TRONDHEIM LUFTHAVN", "country": "no", "geoLat": 63.457, "geoLon": 10.924},
            "returnLocation": {"name": "OSLO LUFTHAVN", "country": "no", "geoLat": 60.195, "geoLon": 11.100},
            "carModel": model, "distance": 505.5, "travelTime": 415,
        }]
    }], "NO", "https://hertzfreerider.no/no-no/")[0]


class ClassificationTest(unittest.TestCase):
    def test_exact_reported_vw_crafter(self):
        ride = example("VW CRAFTER 14M3 4MOTION TDI VA")
        # Display the provider's exact carModel verbatim (including "VW").
        self.assertEqual(ride.vehicle, "VW CRAFTER 14M3 4MOTION TDI VA")
        self.assertEqual(ride.as_event()["vehicle"], "VW CRAFTER 14M3 4MOTION TDI VA")
        self.assertEqual(ride.vehicle_type, "van")
        self.assertEqual(ride.distance_km, 505.5)
        self.assertEqual(ride.drive_minutes, 415.0)
        self.assertEqual(quote_eligibility(ride), "unknown_heavy_vehicle_rate")

    def test_other_commercial_models(self):
        for model in ("Mercedes Sprinter", "Fiat Ducato", "Ford Transit", "VW Transporter", "Toyota Proace", "Renault Master"):
            with self.subTest(model=model):
                self.assertEqual(example(model).vehicle_type, "van")

    def test_small_car_is_not_automatically_van(self):
        self.assertIsNone(example("VW GOLF 1.5 TSI DSG").vehicle_type)

    def test_suv_stays_passenger_car(self):
        self.assertEqual(example("VOLVO XC40 SUV AUT").vehicle_type, "car")

    def test_invalid_provider_metrics_never_guess(self):
        for bad in (-1, float("nan"), True, "not-a-number", None):
            with self.subTest(value=str(bad)):
                payload = [{"routes": [{
                    "id": 123,
                    "pickupLocation": {"name": "Oslo"},
                    "returnLocation": {"name": "Bodø"},
                    "carModel": "CAR", "distance": bad, "travelTime": bad,
                }]}]
                ride = parse_transport_routes(payload, "NO", "https://hertzfreerider.no/")[0]
                self.assertIsNone(ride.distance_km)
                self.assertIsNone(ride.drive_minutes)


if __name__ == "__main__":
    unittest.main()
