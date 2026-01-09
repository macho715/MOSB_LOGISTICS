import type { Location, Shipment, Leg, Event } from "../types/logistics";
import { AuthService } from "./auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

function getAuthHeaders(): HeadersInit {
  const token = AuthService.getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export class LogisticsAPI {
  static async getLocations(): Promise<Location[]> {
    const res = await fetch(`${API_BASE}/api/locations`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      if (res.status === 401) {
        AuthService.logout();
        throw new Error("Authentication required");
      }
      throw new Error(`Failed to fetch locations: ${res.statusText}`);
    }
    return res.json();
  }

  static async getShipments(): Promise<Shipment[]> {
    const res = await fetch(`${API_BASE}/api/shipments`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      if (res.status === 401) {
        AuthService.logout();
        throw new Error("Authentication required");
      }
      if (res.status === 403) {
        throw new Error("Access denied. Insufficient permissions.");
      }
      throw new Error(`Failed to fetch shipments: ${res.statusText}`);
    }
    return res.json();
  }

  static async getLegs(): Promise<Leg[]> {
    const res = await fetch(`${API_BASE}/api/legs`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      if (res.status === 401) {
        AuthService.logout();
        throw new Error("Authentication required");
      }
      throw new Error(`Failed to fetch legs: ${res.statusText}`);
    }
    return res.json();
  }

  static async getEvents(since?: string): Promise<Event[]> {
    const url = since
      ? `${API_BASE}/api/events?since=${encodeURIComponent(since)}`
      : `${API_BASE}/api/events`;
    const res = await fetch(url, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      if (res.status === 401) {
        AuthService.logout();
        throw new Error("Authentication required");
      }
      throw new Error(`Failed to fetch events: ${res.statusText}`);
    }
    return res.json();
  }

  static async postDemoEvent(): Promise<{ ok: boolean; event: Event }> {
    const res = await fetch(`${API_BASE}/api/events/demo`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      if (res.status === 401) {
        AuthService.logout();
        throw new Error("Authentication required");
      }
      throw new Error(`Failed to post demo event: ${res.statusText}`);
    }
    return res.json();
  }
}
