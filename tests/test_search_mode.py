"""Regression tests: pausing a watch stops provider polling and retains setup."""

import unittest

from search_mode import periodic_checks_enabled, search_active
from notifications import notification_content
from filters import Ride


class SearchPauseTests(unittest.TestCase):
    def test_old_profile_stays_on_without_new_option(self):
        self.assertTrue(search_active({"notify_enabled":False}))
        self.assertTrue(periodic_checks_enabled({"scan_interval":30}))

    def test_paused_profile_never_runs_periodically(self):
        self.assertFalse(search_active({"search_active":False}))
        self.assertFalse(periodic_checks_enabled({
            "search_active":False,"scan_mode":"automatic","scan_interval":15,
            "notify_enabled":True,
        }))

    def test_manual_scan_mode_also_disables_scheduled_polling(self):
        self.assertTrue(search_active({"scan_mode":"manual"}))
        self.assertFalse(periodic_checks_enabled({"scan_mode":"manual"}))

    def test_alerts_muting_not_same_as_pausing_watch(self):
        self.assertTrue(periodic_checks_enabled({
            "search_active":True,"notify_enabled":False,
            "scan_mode":"automatic",
        }))

    def test_car_model_has_no_prefixed_emoji_on_separate_line(self):
        ride=Ride("NO","7","TRONDHEIM","OSLO",
                  "VW CRAFTER 14M3 4MOTION TDI VA",
                  "https://hertzfreerider.no/no-no/")
        body=notification_content(ride,"My Watch",language="nb")["message"]
        self.assertIn("\nVW CRAFTER 14M3 4MOTION TDI VA\n",body)
        self.assertNotIn("🚙 VW CRAFTER",body)
        en=notification_content(ride,"My Watch",language="en")["message"]
        self.assertIn("\nVW CRAFTER 14M3 4MOTION TDI VA\n",en)


if __name__=="__main__":
    unittest.main()
