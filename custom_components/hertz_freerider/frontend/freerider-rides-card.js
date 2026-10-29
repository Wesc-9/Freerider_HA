/* Freerider HA: dependency-free Home Assistant Lovelace result card.
 * This is a dashboard card, not a replacement for the standard entity dialog.
 * All source data uses textContent; external links are restricted to the
 * provider's known hosts and cannot embed scripts in the HA interface.
 */
(() => {
  const TYPE = "freerider-rides-card";
  if (customElements.get(TYPE)) return;

  class FreeriderRidesCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._config = { entity: "sensor.freerider_matching_rides" };
      this._hass = null;
      this._signature = "";
      this._sortMode = "recommended";
      this._openMaps = new Set();
      this._showFavorites = false;
      this._message = "";
      this._calculating = new Set();
      const style = document.createElement("style");
      style.textContent = `
        :host { display:block; font-family:var(--paper-font-body1_-_font-family, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif); }
        ha-card { display:block; background:var(--ha-card-background, var(--card-background-color,#fff)); border-radius:20px; overflow:hidden; color:var(--primary-text-color,#222); }
        .wrap { padding:13px; display:grid; gap:10px; }
        .head { display:flex; align-items:center; justify-content:space-between; gap:8px; }
        .title { font-size:17px; font-weight:700; letter-spacing:-.02em; }
        .sub { font-size:12px; color:var(--secondary-text-color,#777); line-height:1.5; }
        .pill { background:var(--secondary-background-color,#f1f1f1); border-radius:999px; padding:7px 11px; font-weight:650; font-size:12px; white-space:nowrap; }
        .ride { border:1px solid var(--divider-color,#e7e7e7); border-radius:14px; padding:12px; display:grid; gap:8px; background:var(--card-background-color,#fff); }
        .route { font-size:13px; font-weight:500; line-height:1.45; color:var(--secondary-text-color,#777); overflow-wrap:anywhere; }
        .vehicle { color:var(--primary-text-color,#222); font-size:16px; font-weight:750; line-height:1.35; margin-bottom:5px; overflow-wrap:anywhere; }
        .metrics { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:6px; }
        .label { font-size:10px; color:var(--secondary-text-color,#777); display:block; margin-bottom:2px; }
        .value { font-size:12px; font-weight:600; overflow-wrap:anywhere; }
        .toll { border-radius:9px; background:var(--secondary-background-color,#f6f6f6); padding:8px 10px; display:flex; align-items:center; justify-content:space-between; gap:12px; }
        .toll .value { text-align:right; }
        .notice { color:var(--secondary-text-color,#777); font-size:11px; line-height:1.45; }
        a.book { display:flex; align-items:center; justify-content:center; min-height:40px; border-radius:11px; color:#fff; background:#77654a; text-decoration:none; font-size:13px; font-weight:700; text-align:center; padding:2px 12px; }
        a.book:hover { background:#665338; }
        .toolbar { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
        .chooser { border:1px solid var(--divider-color,#ddd); padding:9px; border-radius:10px; color:var(--primary-text-color); background:var(--card-background-color); font-size:12px; flex:1; min-width:145px; }
        .actions {display:flex; flex-wrap:wrap; gap:7px; }
        .mini { border:1px solid var(--divider-color,#ddd); border-radius:9px; padding:7px 9px; font-size:12px; font-weight:600; background:var(--secondary-background-color,#f7f7f7); color:var(--primary-text-color); cursor:pointer; }
        .mini:focus-visible {outline:2px solid var(--primary-color,#777); }
        .detail { font-size:12px; color:var(--secondary-text-color,#777); }
        .map { width:100%; height:245px; border:1px solid var(--divider-color,#ddd); border-radius:10px; }
        .warning { font-size:12px; font-weight:550; color:var(--warning-color,#995b00); }
        .favorite-area {display:grid; gap:8px; }
        .favorite-entry {border-radius:10px; padding:10px; border:1px solid var(--divider-color,#ddd); font-size:12px; }
        .empty { padding:15px; border-radius:12px; background:var(--secondary-background-color,#f6f6f6); font-size:13px; }
        @media (max-width:400px) {.wrap { padding:13px; } .ride {padding:12px;} }
      `;
      this.shadowRoot.appendChild(style);
    }

    setConfig(config) {
      if (!config || typeof config !== "object") throw Error("Freerider HA: invalid configuration");
      if (config.entity !== undefined && (typeof config.entity !== "string" || !config.entity.startsWith("sensor."))) {
        throw Error("Freerider HA: entity must be a sensor");
      }
      this._config = { entity:"sensor.freerider_matching_rides", ...config };
      this._signature = "";
      this._render();
    }

    set hass(hass) {
      this._hass = hass;
      const state = hass?.states?.[this._config.entity];
      const signature = JSON.stringify([hass?.language, state?.state, state?.last_updated, state?.attributes]);
      if (signature !== this._signature) {
        this._signature = signature;
        this._render();
      }
    }

    getCardSize() { return 4; }
    static getStubConfig() { return { entity:"sensor.freerider_matching_rides" }; }

    _text(tag, cls, value) {
      const node = document.createElement(tag);
      if (cls) node.className = cls;
      node.textContent = value == null ? "" : String(value);
      return node;
    }

    _safeUrl(ride) {
      const fallback = ride?.country === "SE" ? "https://hertzfreerider.se/sv-se/" : "https://hertzfreerider.no/no-no/";
      try {
        const url = new URL(ride?.listing_source_status === "stale" ? fallback : (ride?.booking_url || fallback));
        if (url.protocol !== "https:" || !["hertzfreerider.no","www.hertzfreerider.no","hertzfreerider.se","www.hertzfreerider.se"].includes(url.hostname))
          return fallback;
        return url.href;
      } catch (_) { return fallback; }
    }

    _date(iso) {
      if (typeof iso !== "string" || !iso) return "—";
      const matched = iso.match(/^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}))?/);
      if (!matched) return iso;
      return matched[3]+"."+matched[2]+"."+matched[1]+(matched[4] ? " "+matched[4]+":"+matched[5] : "");
    }

    _metric(parent, name, value) {
      const area = document.createElement("div");
      area.append(this._text("span","label",name), this._text("div","value",value));
      parent.append(area);
    }

    _coord(value) {
      return typeof value === "number" && Number.isFinite(value) ? value : null;
    }

    _routeUrl(ride) {
      const a=[this._coord(ride.pickup_lat),this._coord(ride.pickup_lon)];
      const b=[this._coord(ride.return_lat),this._coord(ride.return_lon)];
      if (a.concat(b).some(x=>x===null)) return null;
      if (Math.abs(a[0])>90 || Math.abs(b[0])>90 || Math.abs(a[1])>180 || Math.abs(b[1])>180) return null;
      return "https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route="+
        encodeURIComponent(a.join(",")+";"+b.join(","));
    }

    _mapEmbed(ride) {
      const a=[this._coord(ride.pickup_lat),this._coord(ride.pickup_lon)];
      const b=[this._coord(ride.return_lat),this._coord(ride.return_lon)];
      if (a.concat(b).some(x=>x===null)) return null;
      if (Math.abs(a[0])>90 || Math.abs(b[0])>90 || Math.abs(a[1])>180 || Math.abs(b[1])>180) return null;
      const mid=[(a[0]+b[0])/2,(a[1]+b[1])/2];
      const pad=.3;
      const bbox=[Math.max(-180,Math.min(a[1],b[1])-pad),Math.max(-90,Math.min(a[0],b[0])-pad),
        Math.min(180,Math.max(a[1],b[1])+pad),Math.min(90,Math.max(a[0],b[0])+pad)];
      return "https://www.openstreetmap.org/export/embed.html?bbox="+bbox.join("%2C")+
        "&layer=mapnik&marker="+mid.join("%2C");
    }

    _saveCalendar(ride) {
      // The provider's earliest availability and return deadline describe
      // an UNCONFIRMED window, not a booking. Label it unambiguously.
      const parse=(s) => typeof s === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(s)
        ? s.slice(0,19).replace(/[-:]/g,"").replace("T","T").padEnd(15,"0")
        : null;
      const start=parse(ride.available_at), end=parse(ride.latest_return_at);
      if (!start || !end || end<=start) {
        this._message="Calendar requires provider pickup and return timestamps.";
        this._render();
        return;
      }
      const escape=(v)=>String(v||"").replace(/\\/g,"\\\\").replace(/;/g,"\\;").replace(/,/g,"\\,").replace(/\n/g,"\\n");
      const title="Mulig Freerider-tur (IKKE BESTILT)";
      const description=escape(ride.vehicle+" | "+ride.origin+" → "+ride.destination+
        " | VIKTIG: Bare et mulig tidsvindu, ingen bekreftet reservasjon. Bekreft hentetid og retur hos leverandør. "+this._safeUrl(ride));
      const ics=[
        "BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Freerider HA//EN",
        "BEGIN:VEVENT","UID:"+escape(ride.id||ride.key||"offer")+"@freerider-ha",
        "DTSTAMP:"+new Date().toISOString().replace(/[-:]/g,"").split(".")[0]+"Z",
        "DTSTART:"+start,"DTEND:"+end,
        "SUMMARY:"+escape(title),"LOCATION:"+escape(ride.origin),
        "DESCRIPTION:"+description,"STATUS:TENTATIVE","END:VEVENT","END:VCALENDAR",""
      ].join("\r\n");
      const url=URL.createObjectURL(new Blob([ics],{type:"text/calendar;charset=utf-8"}));
      const link=document.createElement("a");
      link.href=url;link.download="freerider-ikke-bestilt.ics";
      this.shadowRoot.append(link);link.click();link.remove();
      // Defer revocation until after the browser has initiated the download.
      setTimeout(()=>URL.revokeObjectURL(url),1000);
    }

    _localSort(rides, mode) {
      if (mode==="recommended") return rides;
      const hav=(r) => {
        const latitude=this._hass?.config?.latitude;
        const longitude=this._hass?.config?.longitude;
        if (![latitude,longitude,r.pickup_lat,r.pickup_lon].every(x=>typeof x==="number")) return null;
        const rad=(x)=>x*Math.PI/180;
        const dlat=rad(r.pickup_lat-latitude),dlon=rad(r.pickup_lon-longitude);
        const h=Math.sin(dlat/2)**2+Math.cos(rad(latitude))*Math.cos(rad(r.pickup_lat))*Math.sin(dlon/2)**2;
        return 6371*2*Math.asin(Math.min(1,Math.sqrt(h)));
      };
      const get=(r) => {
        if(mode==="short_drive")return r.drive_minutes;
        if(mode==="short_route")return r.distance_km;
        if(mode==="nearest_pickup")return hav(r);
        if(mode==="low_cost")return r.estimated_trip_costs?.known_subtotal_nok;
        if(mode==="best_margin")return r.time_feasibility?.margin_minutes == null
          ? null : -r.time_feasibility.margin_minutes;
        return null;
      };
      return [...rides].sort((a,b) => {
        const av=get(a),bv=get(b);
        if(typeof av!=="number"||!Number.isFinite(av))return 1;
        if(typeof bv!=="number"||!Number.isFinite(bv))return -1;
        return av-bv;
      });
    }

    _makeButton(text,click) {
      const node=this._text("button","mini",text);
      node.type="button";node.addEventListener("click",click);
      return node;
    }

    _estimate(entryId,rideId) {
      if (!entryId || !rideId || this._calculating.has(rideId)) return;
      this._calculating.add(rideId);
      this._message="";
      this._render();
      this._hass.callService("hertz_freerider","estimate_toll",{
        entry_id:entryId,ride_id:rideId,
      }).then(()=>{
        this._message="";
      }).catch((err)=>{
        this._message=String(err?.message||err);
      }).finally(()=>{
        this._calculating.delete(rideId);
        this._render();
      });
    }

    _favorite(entryId,rideId,favorite) {
      if (!entryId || !rideId) return;
      this._hass.callService("hertz_freerider","set_favorite",{
        entry_id:entryId,ride_id:rideId,favorite,
      }).catch((err)=>{this._message="Could not save favorite: "+String(err);this._render();});
    }

    _render() {
      if (!this.shadowRoot || !this._hass || !this._config) return;
      const state = this._hass.states?.[this._config.entity];
      const nb = /^(nb|nn|no)/i.test(this._hass.language || "");
      const tr = (no,en) => nb ? no : en;
      const root = document.createElement("ha-card");
      const content = this._text("div","wrap","");
      const head = this._text("div","head","");
      const titles = document.createElement("div");
      titles.append(this._text("div","title",tr("Tilgjengelige biltilbud","Available car offers")));
      const name = state?.attributes?.search_name || (state?.attributes?.friendly_name || this._config.entity);
      titles.append(this._text("div","sub",name));
      head.append(titles);
      const matches = Number(state?.state);
      head.append(this._text("div","pill",Number.isFinite(matches) ? matches + tr(" treff"," offers") : "—"));
      content.append(head);
      if (!state) {
        content.append(this._text("div","empty",tr("Fant ikke sensoren. Velg riktig «sensor.*_matching_rides» i kortets YAML.","Sensor not found. Set the correct «sensor.*_matching_rides» in card YAML.")));
      } else if (["unavailable","unknown"].includes(state.state)) {
        content.append(this._text("div","empty",tr("Datakilden er utilgjengelig. Siste kjente treff kan være utdaterte.","Data source unavailable. Previously seen cars may be outdated.")));
      } else {
        const raw = Array.isArray(state.attributes?.rides) ? state.attributes.rides : [];
        const toolbar=this._text("div","toolbar","");
        const sort=document.createElement("select");
        sort.className="chooser";
        sort.setAttribute("aria-label",tr("Sorter biltilbud","Sort car offers"));
        const modes=[
          ["recommended",tr("Anbefalt rekkefølge","Recommended order")],
          ["short_drive",tr("Korteste kjøretid","Shortest driving time")],
          ["short_route",tr("Korteste distanse","Shortest distance")],
          ["nearest_pickup",tr("Nærmeste hentested (luftlinje)","Nearest pickup (air distance)")],
          ["low_cost",tr("Laveste kjente kostnad","Lowest known cost")],
          ["best_margin",tr("Størst tidsmargin","Largest time margin")],
        ];
        for(const [value,label] of modes) {
          const option=document.createElement("option");option.value=value;option.textContent=label;
          sort.append(option);
        }
        sort.value=this._sortMode;
        sort.addEventListener("change",()=>{
          this._sortMode=sort.value;this._render();
        });
        toolbar.append(sort);
        toolbar.append(this._makeButton(
          this._showFavorites ? tr("Skjul favoritter","Hide favorites") : tr("Vis favoritter","Show favorites"),
          ()=>{this._showFavorites=!this._showFavorites;this._render();}
        ));
        content.append(toolbar);
        const rides = this._localSort(raw,this._sortMode);
        const favIds=new Set(state.attributes?.favorite_ids||[]);
        const entryId=state.attributes?.entry_id;
        if(this._message)content.append(this._text("div","warning",this._message));
        if(this._showFavorites) {
          const favArea=this._text("div","favorite-area","");
          for(const item of state.attributes?.favorite_offers||[]) {
            const row=this._text("div","favorite-entry","");
            row.append(this._text("div","value",item.vehicle||"Vehicle"));
            row.append(this._text("div","sub",(item.origin||"?")+" → "+(item.destination||"?")));
            if(!raw.some(r=>r.id===item.id))row.append(this._text("div","warning",tr(
              "Ikke i siste treffliste – tilgjengelighet ubekreftet","Not in latest results – availability unconfirmed"
            )));
            row.append(this._makeButton(tr("Fjern favoritt","Remove favorite"),
              ()=>this._favorite(entryId,item.id,false)));
            favArea.append(row);
          }
          if(!favArea.children.length)favArea.append(this._text("div","sub",tr("Ingen lagrede favoritter.","No saved favorites.")));
          content.append(favArea);
        }
        if (!rides.length) content.append(this._text("div","empty",tr("Ingen biler matcher søket akkurat nå.","No matching cars right now.")));
        const km = (x) => typeof x === "number" && x > 0 ? (""+x).replace(".",",")+" km" : "—";
        const duration = (x) => {
          if (typeof x !== "number" || x <= 0) return "—";
          const n=Math.round(x),h=Math.floor(n/60),m=n%60;
          return h ? (nb ? h+" t "+m+" min" : h+"h "+m+"m") : m+" min";
        };
        for (const ride of rides) {
          if (!ride || typeof ride !== "object") continue;
          const card = this._text("section","ride","");
          const label = document.createElement("div");
          // The vehicle is displayed verbatim from the Freerider carModel
          // API field. Do NOT replace it with guessed types like "van".
          label.append(this._text("div","vehicle",ride.vehicle || tr("Bilmodell ikke oppgitt","Vehicle name not provided")));
          label.append(this._text("div","route",(ride.origin || "?")+" → "+(ride.destination || "?")));
          card.append(label);
          const metrics = this._text("div","metrics","");
          this._metric(metrics,tr("Distanse","Distance"),km(ride.distance_km ?? ride.toll_estimate?.distance_km));
          this._metric(metrics,tr("Kjøretid (anslag)","Travel time (estimate)"),duration(ride.drive_minutes ?? ride.toll_estimate?.duration_min));
          this._metric(metrics,tr("Tilgjengelig fra","Available from"),this._date(ride.available_at || ride.date_start));
          this._metric(metrics,tr("Seneste retur","Return deadline"),this._date(ride.latest_return_at));
          card.append(metrics);
          const viability=ride.time_feasibility||{};
          if(viability.status==="comfortable"||viability.status==="tight"||viability.status==="insufficient") {
            const margin=viability.margin_minutes;
            const label=viability.status==="insufficient"
              ? tr("For liten tidsmargin","Insufficient travel window")
              : (viability.status==="tight"?tr("Stram tidsmargin","Tight travel window")
                :tr("Beregnet tidsmargin","Estimated spare time"));
            card.append(this._text("div","warning",label+": "+(margin>=0?"+":"")+margin+" min · "+tr(
              "30 min hente-/leveringsbuffer, ikke bekreftet booking",
              "30 min pickup buffer, not confirmed booking"
            )));
          }
          const toll = this._text("div","toll","");
          toll.append(this._text("span","label",tr("Bompenger","Road tolls")));
          const estimate = ride.toll_estimate;
          let price = tr("Ikke beregnet","Not calculated");
          if (estimate && typeof estimate.amount_nok==="number") {
            price = new Intl.NumberFormat(nb ? "nb-NO" : "en-US", {maximumFractionDigits:0}).format(estimate.amount_nok) + " kr " + tr("(anslag)","(estimate)");
          } else if (ride.vehicle_type==="van" || ride.vehicle_type==="minibus") {
            price = tr("Ukjent takstgruppe","Vehicle toll class unknown");
          }
          toll.append(this._text("div","value",price));
          card.append(toll);
          // Road obstruction status is only sourced from the recommended
          // SVV route snapshot. Not checked != no known problems.
          const road= this._text("div","toll","");
          road.append(this._text("span","label",tr("Veiforhold på ruten","Road conditions")));
          let roadStatus=tr("Ikke kontrollert","Not checked");
          if(estimate?.road_obstructed===true) {
            roadStatus=tr("Hindring meldt – kontroller ruten","Obstruction reported – check route");
          } else if(estimate?.road_obstructed===false) {
            roadStatus=tr("Ingen hindring i rutesvaret","No obstruction in route response");
          }
          road.append(this._text("div","value",roadStatus));
          card.append(road);
          if(estimate?.road_checked_at){
            const ts=String(estimate.road_checked_at);
            card.append(this._text("div","notice",tr(
              "Ruteinformasjon via BompengeAppen: ",
              "Route information via BompengeAppen: "
            )+this._date(ts)+" · "+tr(
              "Ikke fullstendige sanntidsmeldinger.",
              "Not comprehensive live traffic data."
            )));
          }
          const traffic=document.createElement("a");
          traffic.className="detail";
          traffic.href="https://www.vegvesen.no/trafikk";
          traffic.target="_blank";
          traffic.rel="noopener noreferrer";
          traffic.textContent=tr("Åpne offentlig trafikkinformasjon i nettleser",
            "Open public road traffic information in your browser");
          card.append(traffic);
          const costs = ride.estimated_trip_costs || {};
          const fmtNok = (x) => typeof x === "number" && Number.isFinite(x)
            ? new Intl.NumberFormat(nb ? "nb-NO" : "en-US", {maximumFractionDigits:0}).format(x)+" kr"
            : "—";
          if (typeof costs.energy_nok === "number") {
            const energy = this._text("div","toll","");
            energy.append(this._text("span","label",tr("Beregnet drivstoff/lading","Estimated fuel/charging")));
            energy.append(this._text("div","value",fmtNok(costs.energy_nok)));
            card.append(energy);
          }
          if (typeof costs.known_subtotal_nok === "number") {
            const partial = this._text("div","toll","");
            partial.append(this._text("span","label",tr("Kjente kostnader – delanslag","Known costs – partial estimate")));
            partial.append(this._text("div","value",fmtNok(costs.known_subtotal_nok)));
            card.append(partial);
          }
          card.append(this._text("div","notice",tr(
            "Bom kan variere etter bilens tillatte totalvekt, kjørerute og tidspunkt. Drivstoff/lading og ferge kan komme i tillegg.",
            "Tolls vary by vehicle weight, route and timing. Fuel/charging and ferries may cost extra."
          )));
          const direct = ride.direct_booking_link === true && ride.listing_source_status !== "stale";
          const a = this._text("a","book",direct
            ? tr("Åpne bestilling for denne bilen","Open booking for this car")
            : tr("Se bilen på Freerider","View on Freerider"));
          a.href = this._safeUrl(ride);
          a.target = "_blank";
          a.rel = "noopener noreferrer";
          a.setAttribute("aria-label",tr("Åpne hos Freerider","Open at Freerider"));
          card.append(a);
          card.append(this._text("div","notice",tr(
            direct
              ? "Åpner leverandørens bestillingsflyt med bil-ID og foreslått hentetid. Tilgjengelighet må bekreftes hos Freerider."
              : "Bestillingslenke ikke bekreftet for dette tilbudet. Åpner Freerider for manuelt søk.",
            direct
              ? "Opens the provider's booking flow with car ID and suggested pickup time. Availability requires confirmation."
              : "An exact offer link is unavailable. Opens Freerider for manual selection."
          )));
          const actions=this._text("div","actions","");
          if(ride.can_calculate_toll === true) {
            const button=this._makeButton(
              this._calculating.has(ride.id)?tr("Beregner …","Calculating …")
                :tr("Beregn bom og veistatus","Calculate toll and road status"),
              ()=>this._estimate(entryId,ride.id),
            );
            button.disabled=this._calculating.has(ride.id);
            actions.append(button);
          }
          actions.append(this._makeButton(
            favIds.has(ride.id)?"★ "+tr("Favoritt","Favorite"):"☆ "+tr("Lagre favoritt","Save favorite"),
            ()=>this._favorite(entryId,ride.id,!favIds.has(ride.id)),
          ));
          const mapUrl=this._routeUrl(ride);
          if(mapUrl){
            actions.append(this._makeButton(
              this._openMaps.has(ride.id)?tr("Skjul kart","Hide map"):tr("Vis kart","Show map"),
              ()=>{
                if(this._openMaps.has(ride.id))this._openMaps.delete(ride.id);
                else this._openMaps.add(ride.id);
                this._render();
              }
            ));
          }
          actions.append(this._makeButton(
            tr("Legg i kalender (.ics)","Add to calendar (.ics)"),
            ()=>this._saveCalendar(ride),
          ));
          card.append(actions);
          if(mapUrl && this._openMaps.has(ride.id)) {
            const mapSrc=this._mapEmbed(ride);
            if(mapSrc) {
              const map=document.createElement("iframe");
              map.className="map";map.src=mapSrc;map.loading="lazy";
              map.setAttribute("title",tr("Kart over området rundt ruten","Map around the route"));
              map.referrerPolicy="no-referrer";
              card.append(map);
              const link=this._text("a","detail",tr("Åpne veibeskrivelse (OpenStreetMap)","Open road directions (OpenStreetMap)"));
              link.href=mapUrl;link.target="_blank";link.rel="noopener noreferrer";
              card.append(link);
              card.append(this._text("div","notice",tr(
                "Kartet viser området, ikke en bekreftet kjørerute. Veibeskrivelse åpnes separat.",
                "Map shows the area, not a verified driving route. Directions open separately."
              )));
            }
          }
          content.append(card);
        }
        if (Number(state.state)>rides.length) content.append(this._text("div","sub",tr("Viser de 20 første treffene. Filtrer søket for å se flere.","Showing the first 20 offers. Narrow the search to see more.")));
        if (state.attributes?.source_errors && Object.keys(state.attributes.source_errors).length) {
          content.append(this._text("div","notice",tr("En eller flere datakilder har feil. Resultatene kan være ufullstendige.","Some data sources failed. Results may be incomplete.")));
        }
        content.append(this._text("div","sub",tr("Oppdateres automatisk når Freerider-sensoren endres.","Updates automatically with the Freerider sensor.")));
      }
      root.append(content);
      this.shadowRoot.replaceChildren(this.shadowRoot.querySelector("style"),root);
    }
  }
  customElements.define(TYPE, FreeriderRidesCard);
  window.customCards = window.customCards || [];
  if (!window.customCards.some(x => x.type===TYPE)) window.customCards.push({
    type: TYPE, name: "Freerider HA · Tilgjengelige biler",
    description: "Vis matchende Freerider-tilbud med bil, rute, km, kjøretid og bomstatus.",
    preview: false
  });
})();
