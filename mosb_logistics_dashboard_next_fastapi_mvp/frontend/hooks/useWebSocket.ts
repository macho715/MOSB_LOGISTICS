import { useEffect, useRef, useState } from "react";
import type { Event, LocationStatus } from "../types/logistics";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
const WS_URL = API_BASE.replace(/^http/, "ws");
const DEFAULT_RECONNECT_DELAY = 3000;
const DEFAULT_MAX_RECONNECT_ATTEMPTS = 10;
const MAX_BACKOFF_MULTIPLIER = 5;

const STATUS_VALUES: Event["status"][] = [
  "PLANNED",
  "IN_TRANSIT",
  "ARRIVED",
  "DELAYED",
  "HOLD",
];

function toNumber(value: unknown): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function normalizeEvent(payload: any): Event | null {
  if (!payload || typeof payload !== "object") return null;
  const status = payload.status as Event["status"];
  if (!STATUS_VALUES.includes(status)) return null;
  if (!payload.event_id || !payload.ts || !payload.shpt_no || !payload.location_id) return null;
  return {
    event_id: String(payload.event_id),
    ts: String(payload.ts),
    shpt_no: String(payload.shpt_no),
    status,
    location_id: String(payload.location_id),
    lat: toNumber(payload.lat),
    lon: toNumber(payload.lon),
    remark: typeof payload.remark === "string" ? payload.remark : "",
  };
}

function readNumberSetting(value: string | undefined, fallback: number): number {
  const n = Number.parseInt(value || "", 10);
  return Number.isFinite(n) ? n : fallback;
}

export function useWebSocket(
  onEvent: (event: Event) => void,
  onLocationStatus?: (status: LocationStatus) => void
) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closedByUser = useRef(false);
  const onEventRef = useRef(onEvent);
  const onLocationStatusRef = useRef(onLocationStatus);

  useEffect(() => {
    onEventRef.current = onEvent;
    onLocationStatusRef.current = onLocationStatus;
  }, [onEvent, onLocationStatus]);

  useEffect(() => {
    const reconnectDelay = readNumberSetting(
      process.env.NEXT_PUBLIC_WS_RECONNECT_DELAY,
      DEFAULT_RECONNECT_DELAY,
    );
    const maxReconnectAttempts = readNumberSetting(
      process.env.NEXT_PUBLIC_WS_MAX_RECONNECT_ATTEMPTS,
      DEFAULT_MAX_RECONNECT_ATTEMPTS,
    );

    const scheduleReconnect = () => {
      if (reconnectAttempts.current >= maxReconnectAttempts) {
        setError("Max reconnection attempts reached");
        return;
      }
      reconnectAttempts.current += 1;
      const multiplier = Math.min(reconnectAttempts.current, MAX_BACKOFF_MULTIPLIER);
      const delay = reconnectDelay * multiplier;
      reconnectTimer.current = setTimeout(connect, delay);
    };

    const connect = () => {
      if (closedByUser.current) return;
      try {
        const ws = new WebSocket(`${WS_URL}/ws/events`);
        wsRef.current = ws;

        ws.onopen = () => {
          setConnected(true);
          setError(null);
          reconnectAttempts.current = 0;
        };

        ws.onerror = () => {
          setError("WebSocket connection error");
        };

        ws.onclose = () => {
          setConnected(false);
          if (!closedByUser.current) scheduleReconnect();
        };

        ws.onmessage = (msg) => {
          try {
            const data = JSON.parse(msg.data);
            if (data?.type === "event" && data.payload) {
              const event = normalizeEvent(data.payload);
              if (event) onEventRef.current(event);
              return;
            }
            if (data?.type === "location_status" && data.payload) {
              if (onLocationStatusRef.current) {
                onLocationStatusRef.current(data.payload as LocationStatus);
              }
              return;
            }
          } catch {
            // Ignore parse errors to avoid crashing the UI.
          }
        };
      } catch {
        setError("Failed to create WebSocket");
      }
    };

    connect();

    return () => {
      closedByUser.current = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return { connected, error };
}
