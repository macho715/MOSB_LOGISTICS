import React, { useEffect, useMemo } from "react";
import ClientOnlyMap from "./ClientOnlyMap";
import { useClientOnlyGeofences } from "../../hooks/useClientOnlyGeofences";
import { useBatchedClientOnlyWs } from "../../hooks/useBatchedClientOnlyWs";
import { useClientOnlyStore } from "../../store/useClientOnlyStore";
import { LogisticsAPI } from "../../lib/api";
import { AuthService } from "../../lib/auth";
import type { Event } from "../../types/logistics";
import type { LiveEvent } from "../../types/clientOnly";

function convertEventToLiveEvent(event: Event): LiveEvent {
  return {
    id: event.event_id,
    ts: event.ts,
    position: [event.lon, event.lat] as [number, number],
    shpt_no: event.shpt_no,
    meta: {
      status: event.status,
      location_id: event.location_id,
      remark: event.remark,
    },
  };
}

function getWsUrl(): string {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
  const wsUrl = apiBase.replace(/^http/, "ws");
  return `${wsUrl}/ws/events`;
}

export default function ClientOnlyDashboard() {
  useClientOnlyGeofences("/data/geofence.json");

  useEffect(() => {
    const loadInitialData = async () => {
      if (!AuthService.isAuthenticated()) return;
      try {
        const [locations, legs, events] = await Promise.all([
          LogisticsAPI.getLocations(),
          LogisticsAPI.getLegs(),
          LogisticsAPI.getEvents(),
        ]);

        const { setLocations, setLegs, ingestEvents } = useClientOnlyStore.getState();
        setLocations(locations);
        setLegs(legs);
        ingestEvents(events.map(convertEventToLiveEvent));
      } catch (err) {
        console.error("Failed to load initial data:", err);
      }
    };

    loadInitialData();
  }, []);

  const ui = useClientOnlyStore((s) => s.ui);
  const setUi = useClientOnlyStore((s) => s.setUi);
  const pruneOldEvents = useClientOnlyStore((s) => s.pruneOldEvents);
  const shipments = useClientOnlyStore((s) => Object.values(s.shipmentsByNo));
  const eventsCount = useClientOnlyStore((s) => s.eventIds.length);

  const kpis = useMemo(() => {
    let planned = 0;
    let inTransit = 0;
    let arrived = 0;
    let delayed = 0;
    let hold = 0;
    let unknown = 0;
    for (const s of shipments) {
      switch (s.status ?? "UNKNOWN") {
        case "PLANNED":
          planned += 1;
          break;
        case "IN_TRANSIT":
          inTransit += 1;
          break;
        case "ARRIVED":
          arrived += 1;
          break;
        case "DELAYED":
          delayed += 1;
          break;
        case "HOLD":
          hold += 1;
          break;
        default:
          unknown += 1;
          break;
      }
    }
    return { planned, inTransit, arrived, delayed, hold, unknown, total: shipments.length };
  }, [shipments]);

  useBatchedClientOnlyWs({
    wsUrl: getWsUrl(),
    flushMs: 500,
    token: typeof window !== "undefined" ? AuthService.getToken() : null,
  });

  useEffect(() => {
    const t = window.setInterval(() => pruneOldEvents(Date.now()), 2000);
    return () => window.clearInterval(t);
  }, [pruneOldEvents]);

  return (
    <div style={{ padding: 16 }}>
      <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap", marginBottom: 12 }}>
        <div><b>Client-Only Dashboard</b></div>

        <div>Shipments: <b>{kpis.total}</b></div>
        <div>Planned: <b>{kpis.planned}</b></div>
        <div>In-Transit: <b>{kpis.inTransit}</b></div>
        <div>Arrived: <b>{kpis.arrived}</b></div>
        <div>Delayed: <b>{kpis.delayed}</b></div>
        <div>Hold: <b>{kpis.hold}</b></div>
        <div>Unknown: <b>{kpis.unknown}</b></div>

        <div>Events in window: <b>{eventsCount}</b></div>

        <label style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
          <input
            type="checkbox"
            checked={ui.showGeofenceMask}
            onChange={(e) => setUi({ showGeofenceMask: e.target.checked })}
          />
          Geofence mask
        </label>

        <label style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
          <input
            type="checkbox"
            checked={ui.showHeatmap}
            onChange={(e) => setUi({ showHeatmap: e.target.checked })}
          />
          Heatmap
        </label>

        <label style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
          <input
            type="checkbox"
            checked={ui.showEta}
            onChange={(e) => setUi({ showEta: e.target.checked })}
          />
          ETA wedge
        </label>

        <label style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
          Window (hours):
          <input
            type="number"
            value={ui.hoursWindow}
            min={1}
            max={168}
            onChange={(e) => setUi({ hoursWindow: Number(e.target.value) })}
            style={{ width: 80 }}
          />
        </label>

        <label style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
          Heat filter:
          <select
            value={ui.heatEventType}
            onChange={(e) => setUi({ heatEventType: e.target.value as any })}
          >
            <option value="all">all</option>
            <option value="enter">enter</option>
            <option value="exit">exit</option>
            <option value="move">move</option>
            <option value="unknown">unknown</option>
          </select>
        </label>
      </div>

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <ClientOnlyMap />
      </div>
    </div>
  );
}
