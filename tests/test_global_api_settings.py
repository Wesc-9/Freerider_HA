"""Shared toll credential migration and rotation without Home Assistant runtime."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import unittest

root = Path(__file__).parents[1] / "custom_components/hertz_freerider"
source = (root / "api_settings.py").read_text()
syntax = ast.parse(source)
selected = [node for node in syntax.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))
            and node.name in ("SharedApiSettings", "get_shared_api_settings")]
module = ast.Module(body=[
    ast.ImportFrom(module="__future__",names=[ast.alias(name="annotations")],level=0),
    *selected,
],type_ignores=[])
ast.fix_missing_locations(module)


class FakeStore:
    saved = {}

    def __init__(self, hass, version, key):
        self.key = key

    async def async_load(self):
        return self.saved.get(self.key)

    async def async_save(self, data):
        self.saved[self.key] = dict(data)


class FakeEntry:
    def __init__(self, data, options=None):
        self.data = dict(data)
        self.options = dict(options or {})


class FakeConfigEntries:
    def async_update_entry(self, entry, *, data, options):
        entry.data = data
        entry.options = options


class SharedApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        FakeStore.saved = {}
        self.hass = SimpleNamespace(data={}, config_entries=FakeConfigEntries())
        self.ns = {
            "Store": FakeStore,
            "asyncio": asyncio,
            "DOMAIN": "hertz_freerider",
            "STORE_VERSION": 1,
            "STORE_KEY": "hertz_freerider_global_api_settings",
            "CONF_TOLL_API_KEY": "toll_api_key",
        }
        exec(compile(module, str(root / "api_settings.py"), "exec"), self.ns)
        self.shared = self.ns["get_shared_api_settings"](self.hass)

    async def test_first_legacy_watch_sets_global_key_and_removes_local_secret(self):
        primary = FakeEntry({"watch_name": "One", "toll_api_key": " old_primary "})
        await self.shared.async_import_from_entry(primary)
        self.assertEqual(self.shared.api_key, "old_primary")
        self.assertNotIn("toll_api_key", primary.data)
        self.assertEqual(FakeStore.saved["hertz_freerider_global_api_settings"]["api_key"],
                         "old_primary")

        secondary = FakeEntry({"watch_name": "Two", "toll_api_key": "second_secret"},
                              {"toll_api_key": "third_secret"})
        await self.shared.async_import_from_entry(secondary)
        self.assertEqual(self.shared.api_key, "old_primary")
        self.assertNotIn("toll_api_key", secondary.data)
        self.assertNotIn("toll_api_key", secondary.options)

    async def test_rotation_is_shared_and_blank_does_not_clear(self):
        await self.shared.async_set_key(" new_key ")
        other = self.ns["get_shared_api_settings"](self.hass)
        self.assertIs(other, self.shared)
        self.assertEqual(other.api_key, "new_key")
        await self.shared.async_set_key("")
        self.assertEqual(other.api_key, "new_key")
        await self.shared.async_set_key("", clear=True)
        self.assertIsNone(other.api_key)

    def test_device_flows_never_show_secret_again(self):
        flow = (root / "config_flow.py").read_text()
        self.assertIn("include_api_key=first_setup", flow)
        self.assertIn('menu.insert(0, "api")', flow)
        self.assertIn("if first_watch_entry(self.hass, self.config_entry):", flow)
        self.assertIn("fields = {}", flow)
        self.assertIn('"clear_api_key"', flow)


if __name__ == "__main__":
    unittest.main()
