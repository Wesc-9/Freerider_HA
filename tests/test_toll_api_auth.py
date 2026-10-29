"""API-key safety: no keyless provider calls or secrets in sensor attributes.

Uses a real coroutine extracted from tolls.py and a fake async HTTP session,
so the Bearer header can be verified without Home Assistant or network access.
"""
import ast
import asyncio
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
import unittest

from filters import Ride

root=Path(__file__).parents[1]/"custom_components/hertz_freerider"
toll_code=(root/"tolls.py").read_text()
tree=ast.parse(toll_code)
nodes=[x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))
       and x.name in ("_station_coordinates","async_estimate_toll")]
module=ast.Module(body=[ast.ImportFrom(module="__future__",names=[ast.alias(name="annotations")],level=0),*nodes],type_ignores=[])
ast.fix_missing_locations(module)
namespace={
    "TollLookupError":type("TollLookupError",(Exception,),{}),
    "isfinite":__import__("math").isfinite,
    "datetime":datetime,
    "timezone":timezone,
    "ROUTE_API":"https://bompengeappen.no/api/route",
}


class FakeResponse:
    def __init__(self,status=200):
        self.status=status
    async def __aenter__(self):return self
    async def __aexit__(self,*args):return False
    def raise_for_status(self):pass
    async def json(self,content_type=None):
        return {"_billing":{"routes":[{"tollSmallNoDiscount":43.0}]}}


class FakeSession:
    def __init__(self):self.calls=[]
    def get(self,url,**kwargs):
        self.calls.append((url,kwargs))
        return FakeResponse()


class ApiKeyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session=FakeSession()
        namespace.update({
            "aiohttp":SimpleNamespace(ClientTimeout=lambda **kw:kw, ClientError=Exception),
            "async_get_clientsession":lambda hass:self.session,
            "parse_toll_response":lambda payload,electric:{"amount_nok":43.0},
        })
        exec(compile(module,str(root/"tolls.py"),"exec"),namespace)
        self.ride=Ride(
            "NO","67865","Oslo","Trondheim","VW Golf",
            "https://hertzfreerider.no/no-no/",
            pickup_country="no",return_country="no",
            pickup_lat=59.9,pickup_lon=10.7,
            return_lat=63.4,return_lon=10.4,
        )

    async def test_no_api_key_is_never_keyless(self):
        with self.assertRaisesRegex(namespace["TollLookupError"],"API-nøkkel"):
            await namespace["async_estimate_toll"](None,self.ride)
        self.assertFalse(self.session.calls)

    async def test_key_in_authorization_header_only(self):
        result=await namespace["async_estimate_toll"](
            None,self.ride,api_key=" bka_SECRETTEST ",
        )
        self.assertEqual(result["amount_nok"],43.0)
        self.assertEqual(len(self.session.calls),1)
        url,args=self.session.calls[0]
        self.assertEqual(args["headers"]["Authorization"],"Bearer bka_SECRETTEST")
        self.assertNotIn("SECRETTEST",url)
        self.assertNotIn("SECRETTEST",str(args["params"]))
        self.assertNotIn("SECRETTEST",str(result))

    def test_credential_never_published_as_sensor_filter(self):
        sensor=(root/"sensor.py").read_text()
        self.assertIn('if key != "toll_api_key"',sensor)
        self.assertIn('"toll_api_configured"',sensor)
        self.assertNotIn('"filters": self.coordinator.settings',sensor)

    def test_register_link_is_actual_free_key_portal(self):
        import json
        for p in ("strings.json","translations/nb.json","translations/en.json"):
            data=json.loads((root/p).read_text())
            self.assertIn("https://bompengeappen.no/api-portal",
                          data["config"]["step"]["user"]["description"])
            self.assertIn("https://bompengeappen.no/api-portal",
                          data["options"]["step"]["costs"]["description"])


if __name__=="__main__":unittest.main()
