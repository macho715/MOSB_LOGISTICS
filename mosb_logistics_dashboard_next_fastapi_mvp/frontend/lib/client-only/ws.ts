import type { LiveEvent, ClientShipment } from "../../types/clientOnly";

export type WsParsed =
  | { kind: "events"; events: LiveEvent[] }
  | { kind: "shipments"; shipments: ClientShipment[] }
  | { kind: "ping" | "hello" | "unknown" };

function asArray<T>(x: unknown): T[] | null {
  return Array.isArray(x) ? (x as T[]) : null;
}

function convertEventToLiveEvent(event: any): LiveEvent | null {
  if (!event || !event.event_id) return null;
  return {
    id: String(event.event_id),
    ts: event.ts || new Date().toISOString(),
    position: [Number(event.lon) || 0, Number(event.lat) || 0] as [number, number],
    shpt_no: event.shpt_no,
    tracker_id: event.tracker_id,
    meta: {
      status: event.status,
      location_id: event.location_id,
      remark: event.remark,
    },
  };
}

export function parseWsMessage(raw: string): WsParsed {
  let msg: any;
  try {
    msg = JSON.parse(raw);
  } catch {
    return { kind: "unknown" };
  }

  if (msg?.type === "event" && msg?.payload) {
    const liveEvent = convertEventToLiveEvent(msg.payload);
    if (liveEvent) {
      return { kind: "events", events: [liveEvent] };
    }
  }

  if (msg?.type === "ping" || msg?.type === "hello") {
    return { kind: msg.type };
  }

  const events = asArray<LiveEvent>(msg?.events);
  if (events) return { kind: "events", events };

  const shipments = asArray<ClientShipment>(msg?.shipments);
  if (shipments) return { kind: "shipments", shipments };

  if (msg?.type === "shipment" && msg?.data) {
    return { kind: "shipments", shipments: [msg.data as ClientShipment] };
  }

  return { kind: "unknown" };
}
