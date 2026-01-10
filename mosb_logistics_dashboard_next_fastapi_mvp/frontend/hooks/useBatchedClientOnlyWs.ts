import { useEffect, useMemo, useRef } from "react";
import { parseWsMessage } from "../lib/client-only/ws";
import { useClientOnlyStore } from "../store/useClientOnlyStore";
import type { LiveEvent, ClientShipment } from "../types/clientOnly";
import type { LocationStatus } from "../types/logistics";

type Options = {
  wsUrl: string;
  flushMs?: number;
  token?: string | null;
  onLocationStatus?: (status: LocationStatus) => void;
};

function buildWsUrl(base: string, token?: string | null): string {
  if (!token) return base;
  const u = new URL(base);
  u.searchParams.set("token", token);
  return u.toString();
}

export function useBatchedClientOnlyWs(opts: Options) {
  const ingestEvents = useClientOnlyStore((s) => s.ingestEvents);
  const upsertShipments = useClientOnlyStore((s) => s.upsertShipments);

  const flushMs = opts.flushMs ?? 500;

  const eventsBuf = useRef<LiveEvent[]>([]);
  const shipmentsBuf = useRef<ClientShipment[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const onLocationStatusRef = useRef(opts.onLocationStatus);

  // Update ref when callback changes
  useEffect(() => {
    onLocationStatusRef.current = opts.onLocationStatus;
  }, [opts.onLocationStatus]);

  const url = useMemo(() => buildWsUrl(opts.wsUrl, opts.token), [opts.wsUrl, opts.token]);

  useEffect(() => {
    let alive = true;
    let backoffMs = 500;

    const flush = () => {
      if (!alive) return;
      const e = eventsBuf.current;
      const s = shipmentsBuf.current;

      if (e.length) {
        eventsBuf.current = [];
        ingestEvents(e);
      }
      if (s.length) {
        shipmentsBuf.current = [];
        upsertShipments(s);
      }
    };

    const flushTimer = window.setInterval(flush, flushMs);

    const connect = () => {
      if (!alive) return;

      try {
        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => {
          backoffMs = 500;
        };

        ws.onmessage = (ev) => {
          try {
            const data = JSON.parse(String(ev.data));
            // Handle location_status messages
            if (data?.type === "location_status" && data.payload && onLocationStatusRef.current) {
              const status = data.payload as LocationStatus;
              if (status?.location_id && typeof status.occupancy_rate === "number") {
                onLocationStatusRef.current(status);
              }
              return;
            }
          } catch {
            // Fall through to parseWsMessage for other message types
          }

          const parsed = parseWsMessage(String(ev.data));
          if (parsed.kind === "ping" || parsed.kind === "hello") return;
          if (parsed.kind === "events") eventsBuf.current.push(...parsed.events);
          if (parsed.kind === "shipments") shipmentsBuf.current.push(...parsed.shipments);
        };

        ws.onclose = () => {
          wsRef.current = null;
          if (!alive) return;
          window.setTimeout(connect, backoffMs);
          backoffMs = Math.min(backoffMs * 2, 10_000);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch (err) {
        console.error("WS connect failed", err);
        if (!alive) return;
        window.setTimeout(connect, backoffMs);
        backoffMs = Math.min(backoffMs * 2, 10_000);
      }
    };

    connect();

    return () => {
      alive = false;
      window.clearInterval(flushTimer);
      try {
        wsRef.current?.close();
      } catch {
        // ignore
      }
    };
  }, [url, flushMs, ingestEvents, upsertShipments]);
}
