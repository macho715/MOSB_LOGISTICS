import { useEffect, useRef, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
const RECONNECT_DELAY = Number(process.env.NEXT_PUBLIC_WS_RECONNECT_DELAY || "3000");
const MAX_ATTEMPTS = Number(process.env.NEXT_PUBLIC_WS_MAX_RECONNECT_ATTEMPTS || "10");

export function useWebSocket(onMessage: (msg: any) => void) {
  const [status, setStatus] = useState<"DISCONNECTED"|"CONNECTING"|"CONNECTED">("DISCONNECTED");
  const attempts = useRef(0);
  const timerRef = useRef<any>(null);

  useEffect(() => {
    const wsUrl = `${API_BASE.replace("http", "ws")}/ws/events`;

    const connect = () => {
      setStatus("CONNECTING");
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        attempts.current = 0;
        setStatus("CONNECTED");
      };

      ws.onmessage = (evt) => {
        try { onMessage(JSON.parse(evt.data)); } catch {}
      };

      ws.onclose = () => {
        setStatus("DISCONNECTED");
        if (attempts.current >= MAX_ATTEMPTS) return;
        attempts.current += 1;
        timerRef.current = setTimeout(connect, RECONNECT_DELAY);
      };

      ws.onerror = () => { try { ws.close(); } catch {} };
    };

    connect();
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [onMessage]);

  return { status };
}
