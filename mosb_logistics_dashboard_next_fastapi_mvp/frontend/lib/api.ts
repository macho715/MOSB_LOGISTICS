import type { Location, Shipment, Leg, Event } from "../types/logistics";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export class LogisticsAPI {
  static async getLocations(): Promise<Location[]> {
    const res = await fetch(`${API_BASE}/api/locations`);
    if (!res.ok) throw new Error(`Failed to fetch locations: ${res.statusText}`);
    return res.json();
  }

  static async getShipments(): Promise<Shipment[]> {
    const res = await fetch(`${API_BASE}/api/shipments`);
    if (!res.ok) throw new Error(`Failed to fetch shipments: ${res.statusText}`);
    return res.json();
  }

  static async getLegs(): Promise<Leg[]> {
    const res = await fetch(`${API_BASE}/api/legs`);
    if (!res.ok) throw new Error(`Failed to fetch legs: ${res.statusText}`);
    return res.json();
  }

  static async getEvents(since?: string): Promise<Event[]> {
    const url = since
      ? `${API_BASE}/api/events?since=${encodeURIComponent(since)}`
      : `${API_BASE}/api/events`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch events: ${res.statusText}`);
    return res.json();
  }

  static async postDemoEvent(): Promise<{ ok: boolean; event: Event }> {
    const res = await fetch(`${API_BASE}/api/events/demo`, { method: "POST" });
    if (!res.ok) throw new Error(`Failed to post demo event: ${res.statusText}`);
    return res.json();
  }
}
