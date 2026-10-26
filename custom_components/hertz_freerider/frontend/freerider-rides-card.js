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
      const style = document.createElement("style");
      style.textContent = `
        :host { display:block; font-family:var(--paper-font-body1_-_font-family, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif); }
        ha-card { display:block; background:var(--ha-card-background, var(--card-background-color,#fff)); border-radius:20px; overflow:hidden; color:var(--primary-text-color,#222); }
        .wrap { padding:20px; display:grid; gap:14px; }
        .head { display:flex; align-items:center; justify-content:space-between; gap:10px; }
        .title { font-size:19px; font-weight:700; letter-spacing:-.02em; }
        .sub { font-size:12px; color:var(--secondary-text-color,#777); line-height:1.5; }
        .pill { background:var(--secondary-background-color,#f1f1f1); border-radius:999px; padding:7px 11px; font-weight:650; font-size:12px; white-space:nowrap; }
        .ride { border:1px solid var(--divider-color,#e7e7e7); border-radius:16px; padding:15px; display:grid; gap:11px; background:var(--card-background-color,#fff); }
        .route { font-size:13px; font-weight:500; line-height:1.45; color:var(--secondary-text-color,#777); overflow-wrap:anywhere; }
        .vehicle { color:var(--primary-text-color,#222); font-size:16px; font-weight:750; line-height:1.35; margin-bottom:5px; overflow-wrap:anywhere; }
        .metrics { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
        .label { font-size:11px; color:var(--secondary-text-color,#777); display:block; margin-bottom:2px; }
        .value { font-size:13px; font-weight:600; overflow-wrap:anywhere; }
        .toll { border-radius:10px; background:var(--secondary-background-color,#f6f6f6); padding:10px 12px; display:flex; align-items:center; justify-content:space-between; gap:12px; }
        .toll .value { text-align:right; }
        .notice { color:var(--secondary-text-color,#777); font-size:11px; line-height:1.45; }
        a.book { display:flex; align-items:center; justify-content:center; min-height:40px; border-radius:11px; color:#fff; background:#77654a; text-decoration:none; font-size:13px; font-weight:700; text-align:center; padding:2px 12px; }
        a.book:hover { background:#665338; }
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
        const rides = Array.isArray(state.attributes?.rides) ? state.attributes.rides : [];
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
          this._metric(metrics,tr("Distanse","Distance"),km(ride.distance_km));
          this._metric(metrics,tr("Kjøretid (anslag)","Travel time (estimate)"),duration(ride.drive_minutes));
          this._metric(metrics,tr("Tilgjengelig fra","Available from"),this._date(ride.available_at || ride.date_start));
          this._metric(metrics,tr("Seneste retur","Return deadline"),this._date(ride.latest_return_at));
          card.append(metrics);
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
