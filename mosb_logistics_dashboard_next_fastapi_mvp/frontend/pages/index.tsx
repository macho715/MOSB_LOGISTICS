import { useCallback, useEffect, useMemo, useState } from "react";
import DeckGL from "@deck.gl/react";
import { ScatterplotLayer, ArcLayer } from "@deck.gl/layers";
import maplibregl from "maplibre-gl";

import { AuthService, User } from "../lib/auth";
import { LogisticsAPI } from "../lib/api";
import { Login } from "../components/Login";
import { useWebSocket } from "../hooks/useWebSocket";
import type { Event, Location } from "../types/logistics";

function toNum(value: unknown): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function colorForType(t: Location["type"]): [number, number, number, number] {
  const m: Record<string,[number,number,number,number]> = {
    MOSB: [255, 0, 0, 220],
    WH: [138, 43, 226, 210],
    PORT: [0, 128, 255, 210],
    BERTH: [0, 180, 255, 210],
    SITE: [255, 99, 71, 210],
  };
  return m[t] || [120,120,120,200];
}

function colorForStatus(s: Event["status"]): [number, number, number, number] {
  const m: Record<string,[number,number,number,number]> = {
    PLANNED: [180,180,180,180],
    IN_TRANSIT: [30,144,255,200],
    ARRIVED: [0,200,83,200],
    DELAYED: [255,140,0,220],
    HOLD: [220,20,60,220],
  };
  return m[s] || [180,180,180,180];
}

const baseKpiCounts: Record<Event["status"], number> = {
  PLANNED: 0,
  IN_TRANSIT: 0,
  ARRIVED: 0,
  DELAYED: 0,
  HOLD: 0,
};

const initialViewState = {
  longitude: 54.458570,
  latitude: 24.328853,
  zoom: 9.6,
  pitch: 0,
  bearing: 0,
};

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [locations, setLocations] = useState<Location[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [selected, setSelected] = useState<string>("");

  useEffect(() => {
    let active = true;
    const initAuth = async () => {
      if (!AuthService.isAuthenticated()) {
        if (active) setAuthReady(true);
        return;
      }
      try {
        const me = await AuthService.getCurrentUser();
        if (!active) return;
        setUser(me);
      } catch (err) {
        if (!active) return;
        setAuthError(err instanceof Error ? err.message : "Auth failed");
      } finally {
        if (active) setAuthReady(true);
      }
    };
    void initAuth();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    if (!user) return () => {
      active = false;
    };
    const load = async () => {
      try {
        const [locs, evs] = await Promise.all([
          LogisticsAPI.getLocations(),
          LogisticsAPI.getEvents(),
        ]);
        if (!active) return;
        setLocations(locs || []);
        setEvents(evs || []);
        if ((evs || []).length > 0) setSelected((evs[0]?.shpt_no) || "");
      } catch (err) {
        if (!active) return;
        const message = err instanceof Error ? err.message : "Failed to load data";
        setAuthError(message);
        if (message.toLowerCase().includes("authentication")) {
          AuthService.logout();
          setUser(null);
        }
      }
    };
    void load();
    return () => {
      active = false;
    };
  }, [user]);

  const handleWsEvent = useCallback((event: Event) => {
    if (!user) return;
    setEvents(prev => [event, ...prev].slice(0, 500));
  }, [user]);

  useWebSocket(handleWsEvent);

  const latestByShipment = useMemo(() => {
    const map = new Map<string, Event>();
    const sorted = [...events].sort((a,b) => (a.ts < b.ts ? 1 : -1));
    for (const e of sorted) {
      if (!map.has(e.shpt_no)) map.set(e.shpt_no, e);
    }
    return map;
  }, [events]);

  const kpis = useMemo(() => {
    const counts = { ...baseKpiCounts };
    for (const e of latestByShipment.values()) {
      counts[e.status] = counts[e.status] + 1;
    }
    const total = Array.from(latestByShipment.values()).length;
    return { ...counts, total };
  }, [latestByShipment]);

  const arcs = useMemo(() => {
    // Simple arc: last event -> MOSB (for demo). Replace with legs model for accurate routing.
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
      onClick: info => {
        const d = info.object as any;
        if (d?.location_id) {
          // noop for now
        }
      }
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
    })
  ];

  useEffect(() => {
    // MapLibre instance
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

  const handleLoginSuccess = () => {
    const cached = AuthService.getCachedUser();
    if (cached) {
      setUser(cached);
      setAuthError(null);
    } else {
      setAuthError("Login succeeded but user cache missing");
    }
  };

  const handleLogout = () => {
    AuthService.logout();
    setUser(null);
    setLocations([]);
    setEvents([]);
    setSelected("");
    setAuthError(null);
  };

  if (!authReady) {
    return (
      <div style={{ padding: 16 }}>
        <div className="small">Authenticating...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div style={{ padding: 16 }}>
        {authError && (
          <div style={{ color: "#ff6b6b", marginBottom: 12 }}>{authError}</div>
        )}
        <Login onLoginSuccess={handleLoginSuccess} />
      </div>
    );
  }

  const canPostDemo = user.role === "OPS" || user.role === "ADMIN";

  return (
    <div style={{ padding: 16 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
        <div style={{ fontSize: 18, fontWeight: 700 }}>MOSB Logistics Live Map (Next.js + Deck.gl)</div>
        <div className="small">sleek UI / real-time-ready</div>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}>
        <div className="small">Signed in as {user.username} ({user.role})</div>
        <button
          onClick={handleLogout}
          style={{
            padding: "6px 10px",
            borderRadius: 10,
            border: "1px solid rgba(255,255,255,0.12)",
            background: "rgba(255,255,255,0.06)",
            color: "#e6edf3",
          }}
        >
          Logout
        </button>
      </div>
      {authError && (
        <div style={{ color: "#ff6b6b", marginTop: 10 }}>{authError}</div>
      )}

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
          <select value={selected} onChange={(e) => setSelected(e.target.value)} style={{ width: "100%", padding: 8, borderRadius: 10 }}>
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
              onClick={() => void LogisticsAPI.postDemoEvent()}
              disabled={!canPostDemo}
              style={{ width: "100%", padding: 10, borderRadius: 12, border: "1px solid rgba(255,255,255,0.12)", background: "rgba(255,255,255,0.06)", color: "#e6edf3" }}
            >
              Demo: Push Event (backend)
            </button>
            {!canPostDemo && (
              <div className="small" style={{ marginTop: 6 }}>
                Demo event is restricted to OPS/ADMIN roles.
              </div>
            )}
            <div className="small" style={{ marginTop: 6 }}>For production: replace demo endpoint with WMS/ERP/GPS/Port feeds.</div>
          </div>
        </div>
      </div>
    </div>
  );
}
