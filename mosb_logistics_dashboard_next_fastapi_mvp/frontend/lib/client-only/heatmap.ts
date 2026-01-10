import type { AnnotatedEvent, HeatPoint } from "../../types/clientOnly";

export type HeatmapFilter = {
  sinceMs: number;
  eventType?: "all" | "enter" | "exit" | "move" | "unknown";
  zoneId?: string | "all";
};

function clampInt(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, Math.round(n)));
}

export function buildHeatPoints(events: AnnotatedEvent[], f: HeatmapFilter): HeatPoint[] {
  const eventType = f.eventType ?? "all";
  const zoneId = f.zoneId ?? "all";

  const out: HeatPoint[] = [];
  for (const e of events) {
    if (e.ts_ms < f.sinceMs) continue;
    if (eventType !== "all" && e.event_type !== eventType) continue;
    if (zoneId !== "all" && e.zone_id !== zoneId) continue;

    const status = e.meta?.status as string | undefined;
    let weight = 1;
    if (status === "DELAYED") weight = 5;
    else if (status === "HOLD") weight = 3;
    else if (status === "IN_TRANSIT") weight = 2;
    else if (status === "ARRIVED") weight = 1;

    if (e.event_type === "enter") weight *= 1.5;
    else if (e.event_type === "exit") weight *= 1.2;

    out.push({
      position: e.position,
      weight: clampInt(weight, 1, 255),
    });
  }
  return out;
}
