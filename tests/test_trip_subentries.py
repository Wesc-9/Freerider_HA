"""Trip subentries: backward-compatible watch identity and independent settings."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

root = Path(__file__).parents[1] / "custom_components/hertz_freerider"
source = (root / "trip_profiles.py").read_text()
tree = ast.parse(source)
selected = [
    node for node in tree.body
    if isinstance(node, (ast.ClassDef, ast.FunctionDef))
    and node.name in (
        "TripProfile", "has_legacy_watch", "trip_profiles",
        "all_watch_profiles", "update_watch_setting",
    )
]
module = ast.Module(body=[
    ast.ImportFrom(
        module="__future__", names=[ast.alias(name="annotations")],
        level=0
    ),
    *selected,
], type_ignores=[])
ast.fix_missing_locations(module)
namespace = {
    "dataclass": __import__("dataclasses").dataclass,
    "DOMAIN": "hertz_freerider",
    "SUBENTRY_TYPE": "trip",
    "LEGACY_WATCH_FIELD": "countries",
}
exec(compile(module, str(root / "trip_profiles.py"), "exec"), namespace)


class FakeConfigEntries:
    def __init__(self, parent):
        self.parent = parent
        self.changes = []

    def async_get_entry(self, entry_id):
        return self.parent if entry_id == self.parent.entry_id else None

    def async_update_subentry(self, parent, subentry, *, data):
        self.changes.append((parent.entry_id, subentry.subentry_id, data))


class TripProfilesTests(unittest.TestCase):
    def test_new_parent_has_independent_trips_and_no_legacy_watch(self):
        trips = {
            "a1": SimpleNamespace(
                subentry_id="a1", title="Oslo - Bergen",
                data={"countries": ["NO"], "origin": ["Oslo"]},
            ),
            "b2": SimpleNamespace(
                subentry_id="b2", title="Bergen - Oslo",
                data={"countries": ["NO"], "origin": ["Bergen"]},
            ),
        }
        parent = SimpleNamespace(
            entry_id="parent", title="Freerider HA", data={}, options={},
            subentries=trips,
            get_subentries_of_type=lambda _kind: list(trips.values()),
        )
        profiles = namespace["all_watch_profiles"](parent)
        self.assertEqual(len(profiles), 2)
        self.assertEqual(profiles[0].entry_id, "parent_a1")
        self.assertEqual(profiles[1].title, "Bergen - Oslo")

        hass = SimpleNamespace(config_entries=FakeConfigEntries(parent))
        namespace["update_watch_setting"](
            hass, profiles[0], "search_active", False,
        )
        self.assertEqual(hass.config_entries.changes[0][0:2], ("parent", "a1"))
        self.assertEqual(hass.config_entries.changes[0][2]["search_active"], False)
        self.assertNotIn("search_active", trips["b2"].data)

    def test_legacy_entry_unchanged(self):
        entry = SimpleNamespace(
            entry_id="previous", title="My old watch",
            data={"countries": ["NO"]}, options={},
            get_subentries_of_type=lambda _kind: [],
        )
        profiles = namespace["all_watch_profiles"](entry)
        self.assertEqual(profiles, [entry])


if __name__ == "__main__":
    unittest.main()
