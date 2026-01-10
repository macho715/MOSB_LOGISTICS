레포 현황을 확인해 하이브리드 통합 계획을 정리 중입니다. 레포 호환형 체크리스트와 파일별 수정 제안부터 제공합니다.


[4 tools called]


## 하이브리드 통합 계획: `/dashboard-client-only` 레포 호환형

### 체크리스트 및 파일별 수정 제안

---

## Phase 4.1 하이브리드 통합 체크리스트

### ✅ Step 1: 의존성 설치 (최소 패키지)

**파일**: `mosb_logistics_dashboard_next_fastapi_mvp/frontend/package.json`

```json
{
  "dependencies": {
    "@deck.gl/core": "^9.0.0",
    "@deck.gl/layers": "^9.0.0",
    "@deck.gl/react": "^9.0.0",
    "@deck.gl/geo-layers": "^9.0.0",
    "@deck.gl/aggregation-layers": "^9.0.0",
    "@deck.gl/extensions": "^9.0.0",
    "@turf/boolean-point-in-polygon": "^7.0.0",
    "@turf/helpers": "^7.0.0",
    "maplibre-gl": "^4.0.0",
    "next": "^16.1.1",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "zustand": "^4.5.2"
  },
  "devDependencies": {
    "@types/node": "20.19.27",
    "@types/react": "18.3.27",
    "@types/react-dom": "^18.2.0",
    "@types/geojson": "^7946.0.13",
    "eslint": "^9.39.2",
    "eslint-config-next": "^16.1.1",
    "typescript": "5.9.3"
  }
}
```

변경 사항:
- ❌ 제거: `@turf/turf`, `@luma.gl/engine`, `@deck.gl/mesh-layers` (번들 크기 절감)
- ✅ 추가: `@turf/boolean-point-in-polygon`, `@turf/helpers` (선택적 의존성)
- ✅ 추가: `@deck.gl/geo-layers` (GeoJsonLayer용)
- ✅ 추가: `zustand` (상태 관리)

---

### ✅ Step 2: 타입 정의 (기존 타입 확장)

**파일**: `mosb_logistics_dashboard_next_fastapi_mvp/frontend/types/clientOnly.ts`

```typescript
import type { Event, ShipmentStatus, Location } from './logistics';

export type LngLat = [number, number]; // [lng, lat]

export type ZoneKind = "MOSB" | "SITE" | "WH" | "PORT" | "BERTH";

export type EventType = "enter" | "exit" | "move" | "unknown";

export interface GeoFenceProperties {
  id: string;
  kind: ZoneKind;
  name?: string;
}

export type GeoFenceGeometry =
  | { type: "Polygon"; coordinates: LngLat[][] }
  | { type: "MultiPolygon"; coordinates: LngLat[][][] };

export interface GeoFenceFeature {
  type: "Feature";
  properties: GeoFenceProperties;
  geometry: GeoFenceGeometry;
}

export interface GeoFenceCollection {
  type: "FeatureCollection";
  features: GeoFenceFeature[];
}

// LiveEvent: WebSocket에서 받는 원본 (기존 Event 호환)
export interface LiveEvent {
  id: string; // event_id
  ts: string | number; // ISO string or epoch ms
  position: LngLat; // [lng, lat]
  shpt_no?: string;
  tracker_id?: string;
  meta?: Record<string, unknown>; // status, location_id, remark 등
}

// AnnotatedEvent: 지오펜스 판정 후
export interface AnnotatedEvent extends LiveEvent {
  ts_ms: number;
  zone_id: string | null;
  zone_kind: ZoneKind | null;
  event_type: EventType;
  weight: number; // 1-255 for heatmap (iOS Safari safe)
}

// ClientShipment: events에서 파생 (CSV에 위치/상태 없음)
export interface ClientShipment {
  shpt_no: string;
  status?: ShipmentStatus; // latest event에서 파생
  current_position?: LngLat; // latest event에서 파생
  speed_kph?: number; // 계산 또는 기본값
  legs?: ShipmentLeg[]; // legs.csv 기반
  updated_at?: string; // latest event ts
}

export interface ShipmentLeg {
  leg_id: string;
  from: { name?: string; position: LngLat };
  to: { name?: string; position: LngLat };
  speed_kph?: number; // mode별 기본값 (ROAD: 60, SEA: 25)
  eta_planned?: string;
}

export interface HeatPoint {
  position: LngLat;
  weight: number; // 1-255
}

// ETA Wedge: SolidPolygonLayer용 (Cone 대신)
export interface EtaWedge {
  id: string;
  shpt_no: string;
  position: LngLat;
  bearing_deg: number;
  uncertainty_m: number; // 반경(미터)
  polygon: LngLat[]; // Closed ring [lng,lat]
  elevation_m: number; // 3D 높이(미터)
}
```

중요 변경:
- ✅ `ClientShipment.status`와 `current_position`은 events에서 파생 (CSV에 없음)
- ✅ `ShipmentLeg.speed_kph`는 mode별 기본값 사용
- ✅ `EtaWedge`는 SolidPolygonLayer 사용 (ConeGeometry 제거)

---

### ✅ Step 3: GeoJSON 데이터 준비

**파일**: `mosb_logistics_dashboard_next_fastapi_mvp/frontend/public/data/geofence.json`

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": "MOSB_ESNAAD",
        "kind": "MOSB",
        "name": "MOSB - Samsung HVDC Lightning Project Esnaad"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [54.44857, 24.318853],
          [54.46857, 24.318853],
          [54.46857, 24.338853],
          [54.44857, 24.338853],
          [54.44857, 24.318853]
        ]]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "id": "DSV_M19",
        "kind": "WH",
        "name": "DSV Warehouse (Musaffah M19)"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [54.4564805, 24.3568127],
          [54.4964805, 24.3568127],
          [54.4964805, 24.3968127],
          [54.4564805, 24.3968127],
          [54.4564805, 24.3568127]
        ]]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "id": "MIRFA_ONSHORE",
        "kind": "SITE",
        "name": "MIR (Mirfa - reference)"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [53.427, 24.101],
          [53.467, 24.101],
          [53.467, 24.141],
          [53.427, 24.141],
          [53.427, 24.101]
        ]]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "id": "SHU_ONSHORE",
        "kind": "SITE",
        "name": "SHU (Shuweihat - reference)"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [52.549199, 24.136936],
          [52.589199, 24.136936],
          [52.589199, 24.176936],
          [52.549199, 24.176936],
          [52.549199, 24.136936]
        ]]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "id": "AGI_OFFSHORE",
        "kind": "SITE",
        "name": "AGI (offshore - reference)"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [53.6263, 24.8229],
          [53.6663, 24.8229],
          [53.6663, 24.8629],
          [53.6263, 24.8629],
          [53.6263, 24.8229]
        ]]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "id": "DAS_OFFSHORE",
        "kind": "SITE",
        "name": "DAS (Das Island - reference)"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [52.843894, 25.131385],
          [52.883894, 25.131385],
          [52.883894, 25.171385],
          [52.843894, 25.171385],
          [52.843894, 25.131385]
        ]]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "id": "PORT_MZ",
        "kind": "PORT",
        "name": "Port (Mina Zayed - reference)"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [54.367718, 24.502483],
          [54.407718, 24.502483],
          [54.407718, 24.542483],
          [54.367718, 24.542483],
          [54.367718, 24.502483]
        ]]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "id": "BERTH_MZ",
        "kind": "BERTH",
        "name": "Berth (Mina Zayed - reference)"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [54.367718, 24.502483],
          [54.387718, 24.502483],
          [54.387718, 24.522483],
          [54.367718, 24.522483],
          [54.367718, 24.502483]
        ]]
      }
    }
  ]
}
```

주요 사항:
- ✅ 각 위치 중심 기준 대략적 사각형 (실제 운영 데이터로 교체 필요)
- ✅ `properties.kind`는 기존 `LocationType`과 호환

---

### ✅ Step 4: 지오펜스 유틸리티 (BBox 최적화)

**파일**: `mosb_logistics_dashboard_next_fastapi_mvp/frontend/lib/client-only/geofence.ts`

```typescript
import booleanPointInPolygon from "@turf/boolean-point-in-polygon";
import { point as turfPoint } from "@turf/helpers";
import type { GeoFenceCollection, GeoFenceFeature, LngLat, ZoneKind } from "../../types/clientOnly";

export type BBox = [minLng: number, minLat: number, maxLng: number, maxLat: number];

export interface GeoFenceIndexed {
  feature: GeoFenceFeature;
  bbox: BBox;
}

export interface GeoFenceIndex {
  items: GeoFenceIndexed[];
}

function isFiniteNumber(n: unknown): n is number {
  return typeof n === "number" && Number.isFinite(n);
}

function computeBBoxPolygon(coords: LngLat[][]): BBox {
  let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity;
  for (const ring of coords) {
    for (const [lng, lat] of ring) {
      if (!isFiniteNumber(lng) || !isFiniteNumber(lat)) continue;
      minLng = Math.min(minLng, lng);
      minLat = Math.min(minLat, lat);
      maxLng = Math.max(maxLng, lng);
      maxLat = Math.max(maxLat, lat);
    }
  }
  return [minLng, minLat, maxLng, maxLat];
}

function computeBBox(feature: GeoFenceFeature): BBox {
  const g = feature.geometry;
  if (g.type === "Polygon") return computeBBoxPolygon(g.coordinates);
  // MultiPolygon
  let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity;
  for (const poly of g.coordinates) {
    const [a, b, c, d] = computeBBoxPolygon(poly);
    minLng = Math.min(minLng, a);
    minLat = Math.min(minLat, b);
    maxLng = Math.max(maxLng, c);
    maxLat = Math.max(maxLat, d);
  }
  return [minLng, minLat, maxLng, maxLat];
}

export function buildGeofenceIndex(collection: GeoFenceCollection): GeoFenceIndex {
  return {
    items: collection.features.map((feature) => ({
      feature,
      bbox: computeBBox(feature),
    })),
  };
}

function inBBox([lng, lat]: LngLat, [minLng, minLat, maxLng, maxLat]: BBox): boolean {
  return lng >= minLng && lng <= maxLng && lat >= minLat && lat <= maxLat;
}

export function findZone(
  position: LngLat,
  index: GeoFenceIndex | null
): { zone_id: string; zone_kind: ZoneKind } | null {
  if (!index) return null;

  const pt = turfPoint(position);

  for (const it of index.items) {
    // BBox pre-filter for performance
    if (!inBBox(position, it.bbox)) continue;
    if (booleanPointInPolygon(pt, it.feature as any)) {
      return { zone_id: it.feature.properties.id, zone_kind: it.feature.properties.kind };
    }
  }
  return null;
}
```

주요 사항:
- ✅ BBox 사전 필터링으로 성능 최적화
- ✅ MultiPolygon 지원

---

### ✅ Step 5: WebSocket 파서 (현재 백엔드 형식 지원)

**파일**: `mosb_logistics_dashboard_next_fastapi_mvp/frontend/lib/client-only/ws.ts`

```typescript
import type { LiveEvent, ClientShipment } from "../../types/clientOnly";

export type WsParsed =
  | { kind: "events"; events: LiveEvent[] }
  | { kind: "shipments"; shipments: ClientShipment[] }
  | { kind: "ping" | "hello" | "unknown" };

function asArray<T>(x: unknown): T[] | null {
  return Array.isArray(x) ? (x as T[]) : null;
}

// 기존 Event 형식 (backend models.py)을 LiveEvent로 변환
function convertEventToLiveEvent(event: any): LiveEvent | null {
  if (!event || !event.event_id) return null;

  return {
    id: event.event_id,
    ts: event.ts || new Date().toISOString(),
    position: [event.lon || 0, event.lat || 0] as [number, number],
    shpt_no: event.shpt_no,
    tracker_id: event.tracker_id,
    meta: {
      status: event.status,
      location_id: event.location_id,
      remark: event.remark
    }
  };
}

export function parseWsMessage(raw: string): WsParsed {
  let msg: any;
  try {
    msg = JSON.parse(raw);
  } catch {
    return { kind: "unknown" };
  }

  // 현재 백엔드 형식: {type: "event", payload: {...}} (main.py)
  if (msg?.type === "event" && msg?.payload) {
    const liveEvent = convertEventToLiveEvent(msg.payload);
    if (liveEvent) {
      return { kind: "events", events: [liveEvent] };
    }
  }

  // 현재 백엔드 형식: {type: "ping"} 또는 {type: "hello"} (main.py)
  if (msg?.type === "ping" || msg?.type === "hello") {
    return { kind: msg.type }; // ping/hello는 무시 (배치 처리에서)
  }

  // 대안 형식 A: { events: [...] }
  const events = asArray<LiveEvent>(msg?.events);
  if (events) return { kind: "events", events };

  // 대안 형식 B: { shipments: [...] }
  const shipments = asArray<ClientShipment>(msg?.shipments);
  if (shipments) return { kind: "shipments", shipments };

  // 대안 형식 C: { type: "shipment", data: {...} }
  if (msg?.type === "shipment" && msg?.data) {
    return { kind: "shipments", shipments: [msg.data as ClientShipment] };
  }

  return { kind: "unknown" };
}
```

주요 변경:
- ✅ 현재 백엔드 `{type: "event", payload: {...}}` 형식 지원
- ✅ `ping`/`hello` 메시지 무시
- ✅ 기존 `Event` 타입을 `LiveEvent`로 변환

---

### ✅ Step 6: 히트맵 유틸리티 (가중치 기반)

**파일**: `mosb_logistics_dashboard_next_fastapi_mvp/frontend/lib/client-only/heatmap.ts`

```typescript
import type { AnnotatedEvent, HeatPoint } from "../../types/clientOnly";

export type HeatmapFilter = {
  sinceMs: number;
  eventType?: "all" | "enter" | "exit" | "move" | "unknown";
  zoneId?: string | "all";
};

function clampInt(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, Math.trunc(n)));
}

/**
 * Returns lightweight points for HeatmapLayer.
 * Keep weights as integers (1..255) to reduce iOS Safari issues (low-precision mode).
 * Weight is based on event status and type (DELAYED > HOLD > IN_TRANSIT > others).
 */
export function buildHeatPoints(events: AnnotatedEvent[], f: HeatmapFilter): HeatPoint[] {
  const eventType = f.eventType ?? "all";
  const zoneId = f.zoneId ?? "all";

  const out: HeatPoint[] = [];
  for (const e of events) {
    if (e.ts_ms < f.sinceMs) continue;
    if (eventType !== "all" && e.event_type !== eventType) continue;
    if (zoneId !== "all" && e.zone_id !== zoneId) continue;

    // Weight based on event status (from meta)
    const status = e.meta?.status as string;
    let weight = 1;
    if (status === "DELAYED") weight = 5;
    else if (status === "HOLD") weight = 3;
    else if (status === "IN_TRANSIT") weight = 2;
    else if (status === "ARRIVED") weight = 1;

    // Boost weight for enter events
    if (e.event_type === "enter") weight *= 1.5;
    else if (e.event_type === "exit") weight *= 1.2;

    out.push({
      position: e.position,
      weight: clampInt(weight, 1, 255), // iOS Safari safe
    });
  }
  return out;
}
```

주요 변경:
- ✅ 상태 기반 가중치 (DELAYED > HOLD > IN_TRANSIT)
- ✅ `enter`/`exit` 이벤트 가중치 증가
- ✅ iOS Safari 안전 범위 (1-255)

---

### ✅ Step 7: ETA Wedge 계산 (events 기반)

**파일**: `mosb_logistics_dashboard_next_fastapi_mvp/frontend/lib/client-only/eta.ts`

```typescript
import type { EtaWedge, LngLat, ClientShipment, AnnotatedEvent } from "../../types/clientOnly";

const EARTH_RADIUS_M = 6371000;

function toRad(d: number): number {
  return (d * Math.PI) / 180;
}

function toDeg(r: number): number {
  return (r * 180) / Math.PI;
}

export function bearingDeg(from: LngLat, to: LngLat): number {
  const [lng1, lat1] = from;
  const [lng2, lat2] = to;

  const φ1 = toRad(lat1);
  const φ2 = toRad(lat2);
  const Δλ = toRad(lng2 - lng1);

  const y = Math.sin(Δλ) * Math.cos(φ2);
  const x = Math.cos(φ1) * Math.sin(φ2) - Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);

  const θ = Math.atan2(y, x);
  const deg = (toDeg(θ) + 360) % 360;
  return deg;
}

/**
 * Great-circle destination point.
 */
export function destination(from: LngLat, bearingDegrees: number, distanceM: number): LngLat {
  const [lng, lat] = from;
  const φ1 = toRad(lat);
  const λ1 = toRad(lng);
  const θ = toRad(bearingDegrees);
  const δ = distanceM / EARTH_RADIUS_M;

  const sinφ2 = Math.sin(φ1) * Math.cos(δ) + Math.cos(φ1) * Math.sin(δ) * Math.cos(θ);
  const φ2 = Math.asin(sinφ2);

  const y = Math.sin(θ) * Math.sin(δ) * Math.cos(φ1);
  const x = Math.cos(δ) - Math.sin(φ1) * Math.sin(φ2);
  const λ2 = λ1 + Math.atan2(y, x);

  return [(toDeg(λ2) + 540) % 360 - 180, toDeg(φ2)];
}

/**
 * Build a wedge polygon (closed ring) centered at `pos`, extending `radiusM` meters,
 * spanning `spreadDeg` degrees around `bearing`.
 */
export function buildWedgePolygon(pos: LngLat, bearing: number, radiusM: number, spreadDeg = 20, steps = 9): LngLat[] {
  const start = bearing - spreadDeg;
  const end = bearing + spreadDeg;

  const pts: LngLat[] = [];
  pts.push(pos);

  for (let i = 0; i < steps; i++) {
    const t = i / (steps - 1);
    const b = start + (end - start) * t;
    pts.push(destination(pos, b, radiusM));
  }

  pts.push(pos); // close
  return pts;
}

function clamp(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n));
}

/**
 * Compute ETA wedges from shipments (events-based).
 * Since CSV has no position/status, we derive from latest events.
 */
export function computeEtaWedges(
  shipments: ClientShipment[],
  events: AnnotatedEvent[],
  nowMs: number
): EtaWedge[] {
  const out: EtaWedge[] = [];

  for (const s of shipments) {
    const pos = s.current_position;
    if (!pos) continue;

    // Find target from legs (if available) or use default direction
    const target = s.legs?.[0]?.to?.position;
    if (!target) continue;

    const brg = bearingDeg(pos, target);

    // Speed from shipment or default by mode
    const speedKph = s.speed_kph ?? 40; // fallback
    const speedMps = (speedKph * 1000) / 3600;

    // Uncertainty model: +/- minutes based on status (from latest event)
    const status = s.status || "IN_TRANSIT";
    const baseUncMin =
      status === "DELAYED" ? 30 :
      status === "IN_TRANSIT" ? 15 :
      10;

    const uncertaintySec = baseUncMin * 60;
    const radiusM = clamp(speedMps * uncertaintySec, 200, 15000);

    // Visual z-height (meters), not physical
    const elevationM = clamp(baseUncMin * 30, 200, 2500);

    out.push({
      id: `eta-${s.shpt_no}`,
      shpt_no: s.shpt_no,
      position: pos,
      bearing_deg: brg,
      uncertainty_m: radiusM,
      polygon: buildWedgePolygon(pos, brg, radiusM, 20, 9),
      elevation_m: elevationM,
    });
  }

  return out;
}
```

주요 변경:
- ✅ `shipments`와 `events`를 함께 받아 상태/위치 파생
- ✅ `SolidPolygonLayer`용 wedge (ConeGeometry 제거)
- ✅ 상태 기반 불확실성 모델

---

### ✅ Step 8: Zustand Store (최적화 + sliding window)

**파일**: `mosb_logistics_dashboard_next_fastapi_mvp/frontend/store/useClientOnlyStore.ts`

```typescript
import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type {
  AnnotatedEvent,
  GeoFenceCollection,
  GeoFenceIndex,
  LiveEvent,
  ClientShipment,
  ShipmentLeg,
  Location,
} from "../types/clientOnly";
import { buildGeofenceIndex, findZone } from "../lib/client-only/geofence";
import type { Event, Leg } from "../types/logistics";

type UiState = {
  showGeofenceMask: boolean;
  showHeatmap: boolean;
  showEta: boolean;
  hoursWindow: number;
  heatEventType: "all" | "enter" | "exit" | "move" | "unknown";
};

type ClientOnlyState = {
  geofences: GeoFenceCollection | null;
  geofenceIndex: GeoFenceIndex | null;

  // Data from API
  locations: Location[];
  legs: Leg[];

  // Client-side state
  shipmentsByNo: Record<string, ClientShipment>;
  eventsById: Record<string, AnnotatedEvent>;
  eventIds: string[];
  lastZoneByKey: Record<string, string | null>;

  ui: UiState;

  // Actions
  setGeofences: (c: GeoFenceCollection) => void;
  setLocations: (locs: Location[]) => void;
  setLegs: (legs: Leg[]) => void;
  upsertShipments: (rows: ClientShipment[]) => void;
  ingestEvents: (rows: LiveEvent[]) => void;
  pruneOldEvents: (nowMs: number) => void;
  setUi: (patch: Partial<UiState>) => void;

  // Derived actions: derive shipments from events
  deriveShipmentsFromEvents: () => void;
};

const MAX_EVENTS = 1000; // Sliding window cap

function tsToMs(ts: string | number): number {
  if (typeof ts === "number" && Number.isFinite(ts)) return ts;
  const ms = Date.parse(String(ts));
  return Number.isFinite(ms) ? ms : Date.now();
}

function clampInt(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, Math.trunc(n)));
}

function deriveKey(e: LiveEvent): string {
  return e.tracker_id ?? e.shpt_no ?? e.id;
}

export const useClientOnlyStore = create<ClientOnlyState>()(
  devtools((set, get) => ({
    geofences: null,
    geofenceIndex: null,
    locations: [],
    legs: [],
    shipmentsByNo: {},
    eventsById: {},
    eventIds: [],
    lastZoneByKey: {},
    ui: {
      showGeofenceMask: true,
      showHeatmap: true,
      showEta: true,
      hoursWindow: 24,
      heatEventType: "all",
    },

    setGeofences: (c) => {
      set(
        {
          geofences: c,
          geofenceIndex: buildGeofenceIndex(c),
        },
        false,
        "setGeofences"
      );
      get().deriveShipmentsFromEvents(); // Re-derive on geofence change
    },

    setLocations: (locs) => {
      set({ locations: locs }, false, "setLocations");
      get().deriveShipmentsFromEvents();
    },

    setLegs: (legs) => {
      set({ legs }, false, "setLegs");
      get().deriveShipmentsFromEvents();
    },

    upsertShipments: (rows) => {
      const prev = get().shipmentsByNo;
      const next = { ...prev };
      for (const s of rows) {
        if (!s?.shpt_no) continue;
        next[s.shpt_no] = { ...prev[s.shpt_no], ...s };
      }
      set({ shipmentsByNo: next }, false, "upsertShipments");
    },

    ingestEvents: (rows) => {
      const { geofenceIndex, eventsById, eventIds, lastZoneByKey } = get();

      const nextEventsById = { ...eventsById };
      const nextEventIds = [...eventIds];
      const nextLastZoneByKey = { ...lastZoneByKey };

      for (const e of rows) {
        if (!e?.id || !e?.position) continue;

        // De-dupe
        if (nextEventsById[e.id]) continue;

        const ts_ms = tsToMs(e.ts);
        const zone = findZone(e.position, geofenceIndex);
        const key = deriveKey(e);

        const prevZone = nextLastZoneByKey[key] ?? null;
        const newZone = zone?.zone_id ?? null;

        // Event type detection: enter/exit/move
        const event_type =
          prevZone === null && newZone !== null ? "enter" :
          prevZone !== null && newZone === null ? "exit" :
          prevZone !== null && newZone !== null && prevZone !== newZone ? "enter" :
          "move";

        nextLastZoneByKey[key] = newZone;

        const annotated: AnnotatedEvent = {
          ...e,
          ts_ms,
          zone_id: zone?.zone_id ?? null,
          zone_kind: zone?.zone_kind ?? null,
          event_type,
          weight: clampInt(1, 1, 255),
        };

        nextEventsById[e.id] = annotated;
        nextEventIds.push(e.id);

        // Enforce max cap
        if (nextEventIds.length > MAX_EVENTS) {
          const oldestId = nextEventIds.shift();
          if (oldestId) delete nextEventsById[oldestId];
        }
      }

      set(
        {
          eventsById: nextEventsById,
          eventIds: nextEventIds,
          lastZoneByKey: nextLastZoneByKey,
        },
        false,
        "ingestEvents"
      );

      // Derive shipments after events update
      get().deriveShipmentsFromEvents();
    },

    pruneOldEvents: (nowMs) => {
      const { ui, eventIds, eventsById } = get();
      const windowMs = ui.hoursWindow * 60 * 60 * 1000;
      const sinceMs = nowMs - windowMs;

      const nextIds: string[] = [];
      const nextById: Record<string, AnnotatedEvent> = {};

      for (const id of eventIds) {
        const e = eventsById[id];
        if (!e) continue;
        if (e.ts_ms < sinceMs) continue;
        nextIds.push(id);
        nextById[id] = e;
      }

      set({ eventIds: nextIds, eventsById: nextById }, false, "pruneOldEvents");
      get().deriveShipmentsFromEvents(); // Re-derive after prune
    },

    setUi: (patch) => set({ ui: { ...get().ui, ...patch } }, false, "setUi"),

    // Derive shipments from events + legs + locations
    deriveShipmentsFromEvents: () => {
      const { eventsById, eventIds, legs, locations } = get();

      // Get latest event per shipment
      const latestByShipment = new Map<string, AnnotatedEvent>();
      for (const id of eventIds.slice().reverse()) { // Reverse to get latest first
        const e = eventsById[id];
        if (!e || !e.shpt_no) continue;
        if (!latestByShipment.has(e.shpt_no)) {
          latestByShipment.set(e.shpt_no, e);
        }
      }

      const locationMap = new Map(locations.map(loc => [loc.location_id, loc]));

      // Build shipments from latest events
      const shipments: Record<string, ClientShipment> = {};
      for (const [shptNo, event] of latestByShipment.entries()) {
        // Find legs for this shipment
        const shipmentLegs = legs
          .filter(l => l.shpt_no === shptNo)
          .map(leg => {
            const fromLoc = locationMap.get(leg.from_location_id);
            const toLoc = locationMap.get(leg.to_location_id);

            // Default speed by mode
            const speedKph = leg.mode === "SEA" ? 25 : leg.mode === "AIR" ? 800 : 60;

            return {
              leg_id: leg.leg_id,
              from: {
                name: fromLoc?.name,
                position: fromLoc ? [fromLoc.lon, fromLoc.lat] as [number, number] : [0, 0],
              },
              to: {
                name: toLoc?.name,
                position: toLoc ? [toLoc.lon, toLoc.lat] as [number, number] : [0, 0],
              },
              speed_kph: speedKph,
              eta_planned: leg.planned_eta,
            } as ShipmentLeg;
          });

        shipments[shptNo] = {
          shpt_no: shptNo,
          status: (event.meta?.status as any) || "IN_TRANSIT",
          current_position: event.position,
          speed_kph: shipmentLegs[0]?.speed_kph || 40,
          legs: shipmentLegs,
          updated_at: new Date(event.ts_ms).toISOString(),
        };
      }

      set({ shipmentsByNo: shipments }, false, "deriveShipmentsFromEvents");
    },
  }))
);
```

주요 변경:
- ✅ `MAX_EVENTS = 1000` 캡 적용
- ✅ `deriveShipmentsFromEvents`: events → shipments 자동 파생
- ✅ `pruneOldEvents` 후 자동 재파생
- ✅ `lastZoneByKey`로 `enter`/`exit` 판정

---

계속 진행하겠습니다. Step 9-14는 다음 메시지에 제공합니다. 이어서 진행할까요?
