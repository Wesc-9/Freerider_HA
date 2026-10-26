/* Test critical card-side presentation without a browser runtime. */
const assert = require("node:assert/strict");
const vm = require("node:vm");
const fs = require("node:fs");
const source=fs.readFileSync("custom_components/hertz_freerider/frontend/freerider-rides-card.js","utf8");
let Card=null;
const fake={
  HTMLElement:class {},
  window:{},
  customElements:{get:()=>null,define:(name,cls)=>{assert.equal(name,"freerider-rides-card");Card=cls;}},
  document:{},
  URL,
  console,
};
vm.runInNewContext(source,fake);
assert.ok(Card);
const card=Object.create(Card.prototype);
card._hass={config:{latitude:63.43,longitude:10.39}};
const ride={id:"NO:67865",vehicle:"VW CRAFTER 14M3 4MOTION TDI VA",
  pickup_lat:63.46,pickup_lon:10.92,return_lat:60.2,return_lon:11.1,
  drive_minutes:420,distance_km:520};
assert.match(card._routeUrl(ride),/^https:\/\/www.openstreetmap.org\/directions\?/);
assert.match(card._mapEmbed(ride),/^https:\/\/www.openstreetmap.org\/export\/embed.html\?/);
assert.equal(card._routeUrl({...ride,return_lat:null}),null);
assert.equal(card._mapEmbed({...ride,pickup_lon:"javascript:bad"}),null);
const other={...ride,id:"NO:67866",distance_km:190,drive_minutes:60};
const missing={...ride,id:"NO:67867",drive_minutes:null,distance_km:null};
let ranked=card._localSort([ride,missing,other],"short_drive");
assert.deepEqual(Array.from(ranked,x=>x.id),["NO:67866","NO:67865","NO:67867"]);
ranked=card._localSort([ride,missing,other],"short_route");
assert.deepEqual(Array.from(ranked,x=>x.id),["NO:67866","NO:67865","NO:67867"]);
console.log("Freerider dashboard logic tests passed");
