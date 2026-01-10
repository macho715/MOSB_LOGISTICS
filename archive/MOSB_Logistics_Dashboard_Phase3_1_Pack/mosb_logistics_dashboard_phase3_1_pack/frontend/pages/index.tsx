import { useEffect, useMemo, useState } from "react";
import DeckGL from "@deck.gl/react";
import { ScatterplotLayer, ArcLayer } from "@deck.gl/layers";
import maplibregl from "maplibre-gl";

import type { Location, Event } from "../types/logistics";
import { api } from "../lib/api";
import { useWebSocket } from "../hooks/useWebSocket";

function toNum(x: any): number {
  const n = Number(x);
  return Number.isFinite(n) ? n : 0;
}

function colorForType(t: string): [number, number, number, number] {
  const m: Record<string,[number,number,number,number]> = {
    MOSB: [255, 0, 0, 220],
    WH: [138, 43, 226, 210],
    PORT: [0, 128, 255, 210],
    BERTH: [0, 180, 255, 210],
    SITE: [255, 99, 71, 210],
  };
  return m[t] || [120,120,120,200];
}

function colorForStatus(s: string): [number, number, number, number] {
  const m: Record<string,[number,number,number,number]> = {
    PLANNED: [180,180,180,180],
    IN_TRANSIT: [30,144,255,200],
    ARRIVED: [0,200,83,200],
    DELAYED: [255,140,0,220],
    HOLD: [220,20,60,220],
  };
  return m[s] || [180,180,180,180];
}

export default function Home() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [selected, setSelected] = useState<string>("");

  useEffect(() => {
    Promise.all([api.locations(), api.events()])
      .then(([locs, evs]) => {
        setLocations(locs);
        setEvents(evs);
        if (evs.length > 0) setSelected(evs[0].shpt_no);
      })
      .catch(() => {});
  }, []);

  const { status: wsStatus } = useWebSocket((msg) => {
    if (msg?.type === "event" && msg?.payload) {
      const e = msg.payload as Event;
      setEvents((prev) => [e, ...prev].slice(0, 500));
      if (!selected) setSelected(e.shpt_no);
    }
  });

  const latestByShipment = useMemo(() => {
    const map = new Map<string, Event>();
    const sorted = [...events].sort((a,b) => (a.ts < b.ts ? 1 : -1));
    for (const e of sorted) if (!map.has(e.shpt_no)) map.set(e.shpt_no, e);
    return map;
  }, [events]);

  const kpis = useMemo(() => {
    const counts: Record<string, number> = { PLANNED: 0, IN_TRANSIT: 0, ARRIVED: 0, DELAYED: 0, HOLD: 0 };
    for (const e of latestByShipment.values()) counts[e.status] = (counts[e.status] || 0) + 1;
    const total = Array.from(latestByShipment.values()).length;
    return { ...counts, total };
  }, [latestByShipment]);

  const arcs = useMemo(() => {
    const mosb = locations.find(l => l.type === "MOSB");
    if (!mosb) return [];
    const out: any[] = [];
    for (const e of latestByShipment.values()) {
      out.push({
        shpt_no: e.shpt_no,
        status: e.status,
        source: [toNum(e.lon), toNum(e.lat)],
        target: [toNum(mosb.lon), toNum(mosb.lat)],
      });
    }
    return out;
  }, [latestByShipment, locations]);

  const layers = [
    new ScatterplotLayer<Location>({
      id: "nodes",
      data: locations,
      pickable: true,
      getPosition: d => [toNum(d.lon), toNum(d.lat)],
      getFillColor: d => colorForType(d.type),
      getRadius: d => (d.type === "MOSB" ? 260 : (d.type === "WH" ? 220 : 180)),
    }),
    new ArcLayer<any>({
      id: "arcs",
      data: arcs,
      getSourcePosition: d => d.source,
      getTargetPosition: d => d.target,
      getSourceColor: d => colorForStatus(d.status),
      getTargetColor: d => colorForStatus(d.status),
      getWidth: 2,
      pickable: true,
    }),
  ];

  const initialViewState = {
    longitude: 54.45857,
    latitude: 24.328853,
    zoom: 9.6,
    pitch: 0,
    bearing: 0,
  };

  useEffect(() => {
    const map = new maplibregl.Map({
      container: "map",
      style: "https://demotiles.maplibre.org/style.json",
      center: [initialViewState.longitude, initialViewState.latitude],
      zoom: initialViewState.zoom,
    });
    return () => map.remove();
  }, []);

  const shpts = Array.from(latestByShipment.keys()).sort();
  const selectedEvents = events.filter(e => e.shpt_no === selected).slice(0, 20);

  return (
    <div style={{ padding: 16 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
        <div style={{ fontSize: 18, fontWeight: 700 }}>MOSB Logistics Dashboard</div>
        <div className="small">WS: {wsStatus}</div>
      </div>

      <div className="kpi">
        <div className="card"><div className="small">Planned</div><div className="big">{kpis.PLANNED || 0}</div></div>
        <div className="card"><div className="small">In Transit</div><div className="big">{kpis.IN_TRANSIT || 0}</div></div>
        <div className="card"><div className="small">Arrived</div><div className="big">{kpis.ARRIVED || 0}</div></div>
        <div className="card"><div className="small">Delayed</div><div className="big">{kpis.DELAYED || 0}</div></div>
        <div className="card"><div className="small">Total</div><div className="big">{kpis.total || 0}</div></div>
      </div>

      <div className="layout">
        <div className="card" style={{ position: "relative" }}>
          <div id="map" style={{ position: "absolute", inset: 0, borderRadius: 14, overflow: "hidden" }} />
          <div style={{ position: "absolute", inset: 0 }}>
            <DeckGL
              initialViewState={initialViewState}
              controller={true}
              layers={layers as any}
              getTooltip={({ object }: any) => object && (object.name || object.shpt_no)}
            />
          </div>
        </div>

        <div className="card panel">
          <div style={{ fontWeight: 700, marginBottom: 10 }}>Shipment Detail</div>
          <select value={selected} onChange={(e) => setSelected(e.target.value)}>
            <option value="">(select)</option>
            {shpts.map(s => <option key={s} value={s}>{s}</option>)}
          </select>

          <div style={{ marginTop: 12, fontWeight: 700 }}>Latest Events</div>
          <table>
            <thead>
              <tr><th>ts</th><th>status</th><th>loc</th><th>remark</th></tr>
            </thead>
            <tbody>
              {selectedEvents.map(e => (
                <tr key={e.event_id}>
                  <td>{e.ts}</td><td>{e.status}</td><td>{e.location_id}</td><td>{e.remark}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div style={{ marginTop: 12 }}>
            <button
              onClick={() => api.demoEvent()}
              style={{ width: "100%", padding: 10, borderRadius: 12, border: "1px solid rgba(255,255,255,0.12)", background: "rgba(255,255,255,0.06)", color: "#e6edf3" }}
            >
              Demo: Push Event
            </button>
            <div className="small" style={{ marginTop: 6 }}>
              Replace demo endpoint with WMS/ERP/GPS/Port feeds.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
