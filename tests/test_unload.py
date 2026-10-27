"""Protect Home Assistant native Disable against recursive config-entry unload.

This loads only the async_unload_entry function's AST, so CI does not need
Home Assistant installed to check our integration-specific lifecycle contract.
"""
import ast
import asyncio
from pathlib import Path
import unittest
from types import SimpleNamespace

SOURCE = Path(__file__).parents[1] / "custom_components/hertz_freerider/__init__.py"
tree = ast.parse(SOURCE.read_text())
fn = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
          and node.name == "async_unload_entry")
module = ast.Module(body=[fn], type_ignores=[])
ast.fix_missing_locations(module)
ns={"DOMAIN":"hertz_freerider","PLATFORMS":["sensor","button","switch"]}
exec(compile(module,str(SOURCE),"exec"),ns)


class _ConfigEntries:
    def __init__(self, succeeds):
        self.succeeds=succeeds
        self.calls=0
    async def async_unload_platforms(self,entry,platforms):
        self.calls+=1
        return self.succeeds


class UnloadTests(unittest.IsolatedAsyncioTestCase):
    async def test_unloads_once_and_leaves_core_to_run_on_unload(self):
        core=_ConfigEntries(True)
        hass=SimpleNamespace(config_entries=core,data={"hertz_freerider":{"watch":"coordinator"}})
        entry=SimpleNamespace(entry_id="watch")
        self.assertTrue(await ns["async_unload_entry"](hass,entry))
        self.assertEqual(core.calls,1)
        self.assertEqual(hass.data["hertz_freerider"],{})

    async def test_failure_does_not_lie_or_remove_live_coordinator(self):
        core=_ConfigEntries(False)
        hass=SimpleNamespace(config_entries=core,data={"hertz_freerider":{"watch":"coordinator"}})
        entry=SimpleNamespace(entry_id="watch")
        self.assertFalse(await ns["async_unload_entry"](hass,entry))
        self.assertEqual(core.calls,1)
        self.assertIn("watch",hass.data["hertz_freerider"])


if __name__=="__main__":
    unittest.main()
