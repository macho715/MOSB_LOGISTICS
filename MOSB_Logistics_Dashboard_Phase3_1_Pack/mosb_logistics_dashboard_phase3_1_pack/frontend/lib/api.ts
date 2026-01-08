import type { Location, Shipment, Leg, Event } from "../types/logistics";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function safeJson<T>(resp: Response): Promise<T> {
  const txt = await resp.text();
  try { return JSON.parse(txt) as T; } catch { throw new Error(txt || "Invalid JSON"); }
}

async function get<T>(path: string): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return safeJson<T>(resp);
}

async function post<T>(path: string, body?: any): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return safeJson<T>(resp);
}

export const api = {
  locations: () => get<Location[]>("/api/locations"),
  shipments: () => get<Shipment[]>("/api/shipments"),
  legs: () => get<Leg[]>("/api/legs"),
  events: (since?: string) => get<Event[]>(`/api/events${since ? `?since=${encodeURIComponent(since)}` : ""}`),
  demoEvent: () => post<Event>("/api/events/demo"),
};
