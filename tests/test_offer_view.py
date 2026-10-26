"""Unit tests for Freerider device-page offer presentation."""

import unittest
from filters import Ride
from offer_view import device_offers, offer_entity_name, offer_entity_state


def sample(id, dest="OSLO LUFTHAVN"):
    return Ride("NO", str(id), "TRONDHEIM LUFTHAVN", dest,
                "VW CRAFTER 14M3 4MOTION TDI VA",
                "https://hertzfreerider.no/no-no/")


class DeviceOfferTests(unittest.TestCase):
    def test_exact_car_name_is_not_replaced_by_van(self):
        ride = sample(67865)
        self.assertEqual(
            offer_entity_name(ride),
            "VW CRAFTER 14M3 4MOTION TDI VA · OSLO LUFTHAVN",
        )
        self.assertEqual(
            offer_entity_state(ride),
            "TRONDHEIM LUFTHAVN → OSLO LUFTHAVN",
        )

    def test_each_actual_offer_gets_a_row_even_if_model_same(self):
        a, b = sample(67865), sample(67866, "OSLO ALNABRU")
        self.assertEqual([r.key for r in device_offers([a, b])],
                         ["NO:67865", "NO:67866"])

    def test_bounded_and_deduplicated(self):
        rides = [sample(i) for i in range(30)]
        self.assertEqual(len(device_offers(rides)), 8)
        self.assertEqual(len(device_offers([rides[0], rides[0], rides[1]])), 2)

    def test_empty_and_removed_offers(self):
        self.assertEqual(device_offers([]), [])
        first = sample(67865)
        second = sample(67866)
        self.assertEqual(device_offers([second]), [second])
        self.assertNotIn(first, device_offers([second]))

    def test_sensor_state_does_not_exceed_ha_limit(self):
        x = Ride("NO", "1", "A" * 300, "B" * 300, "VW CRAFTER",
                 "https://hertzfreerider.no/no-no/")
        self.assertLessEqual(len(offer_entity_state(x)), 255)


if __name__ == "__main__":
    unittest.main()
