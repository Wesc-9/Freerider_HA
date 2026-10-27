"""Pure behavioral checks for 'all dates' and guided date selection.

Avoid importing HA in CI: inspect only the small pure functions from
config_flow.py, with the exact constant values used at runtime.
"""
import ast
from datetime import date
from pathlib import Path
import unittest

path=Path(__file__).parents[1]/"custom_components/hertz_freerider/config_flow.py"
tree=ast.parse(path.read_text())
names={"route_dates","all_dates_default","all_dates_fields","validation_error"}
pure=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
module=ast.Module(body=pure,type_ignores=[])
ast.fix_missing_locations(module)
env={
  "CONF_DATE_START":"date_start","CONF_DATE_END":"date_end",
  "CONF_DATE_MODE":"date_mode","CONF_ALL_DATES":"all_dates",
  "CONF_COUNTRIES":"countries",
  "date":date,
}
exec(compile(module,str(path),"exec"),env)


class AnyDateTests(unittest.TestCase):
    def test_all_dates_is_default_for_fresh_and_legacy_unrestricted_searches(self):
        self.assertTrue(env["all_dates_default"]({}))
        self.assertTrue(env["all_dates_default"]({"date_mode":"any"}))
        self.assertFalse(env["all_dates_default"]({"date_mode":"range"}))
        self.assertFalse(env["all_dates_default"]({"all_dates":False}))

    def test_toggle_on_erases_old_restrictive_dates(self):
        self.assertEqual(env["all_dates_fields"](),{
            "all_dates":True,"date_mode":"any",
            "date_start":None,"date_end":None,
        })

    def test_single_start_day(self):
        self.assertEqual(env["route_dates"]({"date_start":"2026-11-01"}),{
            "date_mode":"single","date_start":"2026-11-01","date_end":None,
        })

    def test_start_end_range(self):
        result=env["route_dates"]({
            "date_start":"2026-11-01","date_end":"2026-11-10",
        })
        self.assertEqual(result["date_mode"],"range")
        self.assertIsNone(env["validation_error"]({
            "countries":["NO"],**result,
        }))

    def test_range_order_guard(self):
        result=env["route_dates"]({
            "date_start":"2026-12-11","date_end":"2026-11-10",
        })
        self.assertEqual(env["validation_error"]({
            "countries":["NO"],**result,
        }),"end_before_start")

    def test_first_date_transitions_to_end_step_in_both_flows(self):
        cls={node.name:node for node in tree.body if isinstance(node,ast.ClassDef)}
        for name, method, target in (
            ("FreeriderConfigFlow","async_step_registration_date_start",
             "async_step_registration_date_end"),
            ("FreeriderOptionsFlow","async_step_edit_date_start",
             "async_step_edit_date_end"),
        ):
            with self.subTest(cls=name):
                fn=next(n for n in cls[name].body
                        if isinstance(n,ast.AsyncFunctionDef) and n.name==method)
                calls=[n.func.attr for n in ast.walk(fn)
                       if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
                self.assertIn(target,calls)


if __name__=="__main__":
    unittest.main()
