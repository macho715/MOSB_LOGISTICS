
## Client-Only 구현 계획 분석 및 현재 프로젝트 비교

현재 프로젝트 상태와 제공된 Client-Only 계획을 비교했습니다.

### 현재 프로젝트 상태 (2026-01-10 기준)

#### 구현된 기능
1. 기본 지도 렌더링: Deck.gl 9.x + MapLibre 4, ScatterplotLayer, ArcLayer
2. WebSocket 연결: FastAPI WebSocket에서 실시간 이벤트 수신
3. 기본 KPI 계산: Planned/InTransit/Arrived/Delayed 상태별 집계
4. 인증/인가: JWT + RBAC
5. 데이터 구조: Locations, Shipments, Legs, Events 기본 타입

#### 미구현 기능
1. 지오펜스 필터링: GeoJSON 로드, 포인트-다각형 검사 없음
2. 히트맵 집계: HeatmapLayer 미사용
3. ETA Cone 계산: SimpleMeshLayer, ConeGeometry 미사용
4. 상태 관리: Zustand/Redux 없음 (React Hooks만 사용)
5. 고급 필터링: 타임라인, 기간 필터, 토글 스위치 없음

### Client-Only 계획 구현 로드맵

계획을 문서화한 마크다운입니다:

```markdown
# MOSB Logistics Dashboard – Client-Only Implementation Plan

**작성일**: 2026-01-10
**프로젝트**: MOSB Logistics Live Map MVP v2
**옵션**: Option A (Client-Only)
**예상 기간**: 2-3주

---

## Executive Summary

**목표**: 백엔드에서 기본 위치/운송 데이터만 전달받고 모든 추가 연산(지오펜스 필터링, 이벤트 타입 판정, 히트맵 집계, ETA Cone 계산)을 브라우저에서 수행합니다.

**핵심 기술 스택**:
- Deck.gl 9.x (MaskExtension, HeatmapLayer, SimpleMeshLayer)
- Next.js 16 (현재 Pages Router 사용 중, App Router로 마이그레이션 고려)
- @turf 라이브러리 (포인트-다각형 검사)
- Zustand 또는 Redux Store (상태 관리)
- @deck.gl/aggregation-layers (HeatmapLayer)
- @deck.gl/mesh-layers (SimpleMeshLayer)
- @luma.gl/engine (ConeGeometry)

**데이터 흐름**: FastAPI WebSocket → 클라이언트 저장 → 브라우저에서 GeoJSON과 결합 → 입출구 판정/밀도 계산/ETA 시각화

**기대 효과**: 서버 부하 감소, 빠른 프로토타이핑, 실시간 시각화

**리스크**: 브라우저 성능 영향, 데이터 보안, 대량 데이터 처리 한계

---

## 현재 프로젝트와의 차이점

### 1. 아키텍처 차이
| 항목 | 현재 상태 | Client-Only 계획 |
|------|----------|-----------------|
| 서버 역할 | 기본 데이터 제공 + 캐싱 | 최소 데이터만 제공 |
| 클라이언트 역할 | 데이터 표시 + 기본 KPI | 모든 도메인 로직 수행 |
| 상태 관리 | React Hooks (useState) | Zustand/Redux Store |
| 라우터 | Pages Router | App Router (권장) |

### 2. 누락된 라이브러리
현재 `package.json`에 없는 필수 패키지:
```json
{
  "dependencies": {
    "@turf/turf": "^7.x.x",
    "@deck.gl/aggregation-layers": "^9.0.0",
    "@deck.gl/mesh-layers": "^9.0.0",
    "@luma.gl/engine": "^9.x.x",
    "zustand": "^4.x.x",
    "react-window": "^1.8.x",
    "react-datepicker": "^4.x.x",
    "@types/react-datepicker": "^4.x.x"
  }
}
```

### 3. 필요한 디렉토리 구조
```
mosb_logistics_dashboard_next_fastapi_mvp/frontend/
├── public/
│   └── data/
│       └── geofence.json          # GeoJSON 지오펜스 데이터 (신규)
├── store/
│   └── useLogisticsStore.ts       # Zustand 스토어 (신규)
├── utils/
│   ├── geofence.ts                # 지오펜스 판정 로직 (신규)
│   ├── heatmap.ts                 # 히트맵 집계 로직 (신규)
│   └── eta.ts                     # ETA 계산 로직 (신규)
├── components/
│   ├── HeatmapToggle.tsx          # 히트맵 토글 (신규)
│   ├── GeofenceToggle.tsx         # 지오펜스 토글 (신규)
│   ├── ETAConeToggle.tsx          # ETA Cone 토글 (신규)
│   └── Timeline.tsx               # 이벤트 타임라인 (신규)
└── hooks/
    └── useGeofence.ts             # 지오펜스 훅 (신규)
```

---

## 단계별 구현 계획

### Phase 4.1: 기반 구조 구축 (1주)

#### 1.1 의존성 설치
```bash
cd mosb_logistics_dashboard_next_fastapi_mvp/frontend
npm install @turf/turf @deck.gl/aggregation-layers @deck.gl/mesh-layers @luma.gl/engine zustand react-window react-datepicker
npm install --save-dev @types/react-datepicker
```

#### 1.2 GeoJSON 데이터 준비
**파일**: `public/data/geofence.json`
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": "MOSB_ESNAAD",
        "type": "MOSB",
        "name": "MOSB - Samsung HVDC Lightning Project Esnaad"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[54.45, 24.32], [54.46, 24.32], [54.46, 24.34], [54.45, 24.34], [54.45, 24.32]]]
      }
    },
    // ... WH, PORT, BERTH, SITE 등 추가
  ]
}
```

#### 1.3 Zustand Store 구현
**파일**: `store/useLogisticsStore.ts`
```typescript
import { create } from 'zustand';
import type { Event, Location, Shipment, Leg } from '../types/logistics';
import type { FeatureCollection } from 'geojson';

interface LogisticsState {
  // Data
  shipments: Shipment[];
  events: Event[];
  locations: Location[];
  legs: Leg[];
  geofences: FeatureCollection | null;

  // Computed
  heatmapData: Array<{ position: [number, number]; weight: number }>;
  annotatedEvents: Array<Event & { zone?: string; event_type?: 'enter' | 'exit' }>;

  // UI State
  showHeatmap: boolean;
  showGeofences: boolean;
  showETACone: boolean;
  filterDateRange: { start: Date | null; end: Date | null };

  // Actions
  setShipments: (data: Shipment[]) => void;
  addEvent: (event: Event) => void;
  setGeofences: (data: FeatureCollection) => void;
  toggleHeatmap: () => void;
  toggleGeofences: () => void;
  toggleETACone: () => void;
  setDateRange: (start: Date | null, end: Date | null) => void;
  computeHeatmap: (hours: number) => void;
  annotateEvents: () => void;
}

export const useLogisticsStore = create<LogisticsState>((set, get) => ({
  // Initial state
  shipments: [],
  events: [],
  locations: [],
  legs: [],
  geofences: null,
  heatmapData: [],
  annotatedEvents: [],
  showHeatmap: false,
  showGeofences: true,
  showETACone: false,
  filterDateRange: { start: null, end: null },

  // Actions
  setShipments: (data) => set({ shipments: data }),
  addEvent: (event) => {
    const events = [...get().events, event].slice(-1000); // Keep last 1000 events
    set({ events });
    get().annotateEvents();
    get().computeHeatmap(24);
  },
  setGeofences: (data) => {
    set({ geofences: data });
    get().annotateEvents();
  },
  toggleHeatmap: () => set((state) => ({ showHeatmap: !state.showHeatmap })),
  toggleGeofences: () => set((state) => ({ showGeofences: !state.showGeofences })),
  toggleETACone: () => set((state) => ({ showETACone: !state.showETACone })),
  setDateRange: (start, end) => set({ filterDateRange: { start, end } }),

  computeHeatmap: (hours) => {
    const { events } = get();
    const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);
    const recentEvents = events.filter(e => new Date(e.ts) >= cutoff);

    // Aggregate by position (simple grid-based)
    const grid = new Map<string, number>();
    recentEvents.forEach(event => {
      const key = `${Math.round(event.lat * 100)},${Math.round(event.lon * 100)}`;
      grid.set(key, (grid.get(key) || 0) + 1);
    });

    const heatmapData = Array.from(grid.entries()).map(([key, count]) => {
      const [lat, lon] = key.split(',').map(Number);
      return {
        position: [lon / 100, lat / 100] as [number, number],
        weight: Math.min(255, count * 10) // Normalize to 0-255
      };
    });

    set({ heatmapData });
  },

  annotateEvents: () => {
    const { events, geofences } = get();
    if (!geofences) {
      set({ annotatedEvents: events });
      return;
    }

    const annotated = events.map(event => {
      const point = { type: 'Feature' as const, geometry: { type: 'Point' as const, coordinates: [event.lon, event.lat] } };

      for (const feature of geofences.features) {
        if (feature.geometry.type === 'Polygon') {
          const inside = booleanPointInPolygon(point, feature);
          if (inside) {
            return {
              ...event,
              zone: feature.properties.id,
              event_type: 'enter' as const
            };
          }
        }
      }

      return { ...event, event_type: 'exit' as const };
    });

    set({ annotatedEvents: annotated });
  }
}));
```

---

### Phase 4.2: 지오펜스 필터링 구현 (3-4일)

#### 2.1 GeoJSON 로더 훅
**파일**: `hooks/useGeofence.ts`
```typescript
import { useEffect } from 'react';
import { useLogisticsStore } from '../store/useLogisticsStore';

export function useGeofence() {
  const setGeofences = useLogisticsStore((state) => state.setGeofences);

  useEffect(() => {
    fetch('/data/geofence.json')
      .then(res => res.json())
      .then(data => setGeofences(data))
      .catch(err => console.error('Failed to load geofences:', err));
  }, [setGeofences]);
}
```

#### 2.2 지오펜스 판정 유틸리티
**파일**: `utils/geofence.ts`
```typescript
import booleanPointInPolygon from '@turf/boolean-point-in-polygon';
import type { Event } from '../types/logistics';
import type { FeatureCollection, Feature, Point } from 'geojson';

export function annotateEvent(
  event: Event,
  geofences: FeatureCollection
): Event & { zone?: string; event_type: 'enter' | 'exit' } {
  const point: Feature<Point> = {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [event.lon, event.lat]
    },
    properties: {}
  };

  for (const feature of geofences.features) {
    if (feature.geometry.type === 'Polygon') {
      if (booleanPointInPolygon(point, feature)) {
        return {
          ...event,
          zone: feature.properties?.id,
          event_type: 'enter'
        };
      }
    }
  }

  return { ...event, event_type: 'exit' };
}
```

#### 2.3 Deck.gl GeoJsonLayer 통합
**파일**: `pages/index.tsx` (수정)
```typescript
import { GeoJsonLayer } from '@deck.gl/layers';
import { MaskExtension } from '@deck.gl/extensions';

// ... existing code ...

const { geofences, showGeofences } = useLogisticsStore();

const layers = [
  // ... existing ScatterplotLayer, ArcLayer ...

  // Geofence Layer (with optional masking)
  ...(geofences && showGeofences ? [
    new GeoJsonLayer({
      id: 'geofences',
      data: geofences,
      pickable: true,
      stroked: true,
      filled: true,
      getFillColor: (f: any) => {
        const type = f.properties?.type;
        const colors: Record<string, [number, number, number, number]> = {
          MOSB: [255, 0, 0, 50],
          WH: [138, 43, 226, 50],
          PORT: [0, 128, 255, 50],
          BERTH: [0, 180, 255, 50],
          SITE: [255, 99, 71, 50]
        };
        return colors[type] || [120, 120, 120, 30];
      },
      getLineColor: [200, 200, 200, 200],
      lineWidthMinPixels: 2
    })
  ] : [])
];

// Optional: Use MaskExtension for filtering
const scatterplotWithMask = new ScatterplotLayer({
  // ... existing config ...
  extensions: geofences ? [new MaskExtension({ maskId: 'geofences' })] : []
});
```

---

### Phase 4.3: 히트맵 집계 구현 (3-4일)

#### 3.1 히트맵 유틸리티
**파일**: `utils/heatmap.ts`
```typescript
import type { Event } from '../types/logistics';

export interface HeatmapDataPoint {
  position: [number, number];
  weight: number;
  timestamp: string;
}

export function aggregateHeatmap(
  events: Event[],
  hours: number = 24,
  gridSize: number = 0.01 // ~1km at equator
): HeatmapDataPoint[] {
  const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);
  const recentEvents = events.filter(e => new Date(e.ts) >= cutoff);

  // Grid-based aggregation
  const grid = new Map<string, { count: number; totalWeight: number }>();

  recentEvents.forEach(event => {
    const latKey = Math.round(event.lat / gridSize);
    const lonKey = Math.round(event.lon / gridSize);
    const key = `${latKey},${lonKey}`;

    const cell = grid.get(key) || { count: 0, totalWeight: 0 };
    cell.count += 1;
    // Weight based on event type (optional)
    const weight = event.status === 'DELAYED' ? 2 : 1;
    cell.totalWeight += weight;
    grid.set(key, cell);
  });

  // Convert to HeatmapLayer format
  return Array.from(grid.entries()).map(([key, value]) => {
    const [latKey, lonKey] = key.split(',').map(Number);
    return {
      position: [lonKey * gridSize, latKey * gridSize] as [number, number],
      weight: Math.min(255, Math.round(value.totalWeight * 10)), // Normalize to 0-255
      timestamp: new Date().toISOString()
    };
  });
}
```

#### 3.2 HeatmapLayer 통합
**파일**: `pages/index.tsx` (수정)
```typescript
import { HeatmapLayer } from '@deck.gl/aggregation-layers';

const { heatmapData, showHeatmap } = useLogisticsStore();

const layers = [
  // ... existing layers ...

  // Heatmap Layer
  ...(showHeatmap && heatmapData.length > 0 ? [
    new HeatmapLayer({
      id: 'heatmap',
      data: heatmapData,
      getPosition: d => d.position,
      getWeight: d => d.weight,
      radiusPixels: 30,
      intensity: 1.0,
      threshold: 0.05,
      colorRange: [
        [0, 0, 255, 0],    // Blue (low)
        [0, 255, 255, 128], // Cyan
        [0, 255, 0, 192],   // Green
        [255, 255, 0, 224], // Yellow
        [255, 0, 0, 255]    // Red (high)
      ]
    })
  ] : [])
];
```

---

### Phase 4.4: ETA Cone 계산 및 렌더링 (4-5일)

#### 4.1 ETA 계산 유틸리티
**파일**: `utils/eta.ts`
```typescript
import type { Leg, Location, Event } from '../types/logistics';
import { ConeGeometry } from '@luma.gl/engine';

export interface ETAConeData {
  leg_id: string;
  midpoint: [number, number, number];
  bearing: number;
  etaHeight: number;
  etaRadius: number;
  minETA: Date;
  maxETA: Date;
  color: [number, number, number, number];
}

export function computeETACones(
  legs: Leg[],
  locations: Location[],
  events: Event[],
  averageSpeed: number = 30 // km/h
): ETAConeData[] {
  const locationMap = new Map(locations.map(loc => [loc.location_id, loc]));

  return legs.map(leg => {
    const from = locationMap.get(leg.from_location_id);
    const to = locationMap.get(leg.to_location_id);

    if (!from || !to) return null;

    // Calculate distance (Haversine formula simplified)
    const lat1 = from.lat * Math.PI / 180;
    const lat2 = to.lat * Math.PI / 180;
    const dLat = (to.lat - from.lat) * Math.PI / 180;
    const dLon = (to.lon - from.lon) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1) * Math.cos(lat2) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    const distance = 6371 * c; // km

    // Calculate ETA
    const hours = distance / averageSpeed;
    const now = new Date();
    const minETA = new Date(now.getTime() + (hours - 0.5) * 60 * 60 * 1000);
    const maxETA = new Date(now.getTime() + (hours + 0.5) * 60 * 60 * 1000);

    // Midpoint and bearing
    const midpoint: [number, number, number] = [
      (from.lon + to.lon) / 2,
      (from.lat + to.lat) / 2,
      100 // altitude in meters
    ];

    const bearing = Math.atan2(
      to.lon - from.lon,
      to.lat - from.lat
    ) * 180 / Math.PI;

    return {
      leg_id: leg.leg_id,
      midpoint,
      bearing,
      etaHeight: hours * 1000, // Height proportional to time
      etaRadius: distance * 100, // Radius proportional to distance
      minETA,
      maxETA,
      color: [255, 140, 0, 180] // Orange with transparency
    };
  }).filter((cone): cone is ETAConeData => cone !== null);
}

// Create shared cone geometry
let sharedConeGeometry: ConeGeometry | null = null;

export function getConeGeometry(): ConeGeometry {
  if (!sharedConeGeometry) {
    sharedConeGeometry = new ConeGeometry({
      radius: 1,
      height: 1,
      cap: true
    });
  }
  return sharedConeGeometry;
}
```

#### 4.2 SimpleMeshLayer 통합
**파일**: `pages/index.tsx` (수정)
```typescript
import { SimpleMeshLayer } from '@deck.gl/mesh-layers';
import { computeETACones, getConeGeometry } from '../utils/eta';

const { legs, locations, events, showETACone } = useLogisticsStore();

const etaCones = useMemo(() => {
  if (!showETACone) return [];
  return computeETACones(legs, locations, events);
}, [legs, locations, events, showETACone]);

const layers = [
  // ... existing layers ...

  // ETA Cone Layer
  ...(showETACone && etaCones.length > 0 ? [
    new SimpleMeshLayer({
      id: 'eta-cones',
      data: etaCones,
      mesh: getConeGeometry(),
      getPosition: d => d.midpoint,
      getOrientation: d => [0, 0, d.bearing],
      getScale: d => [d.etaRadius, d.etaRadius, d.etaHeight],
      getColor: d => d.color,
      pickable: true,
      onClick: (info) => {
        if (info.object) {
          const cone = info.object as ETAConeData;
          console.log(`ETA Range: ${cone.minETA} - ${cone.maxETA}`);
          // Show tooltip or popup
        }
      }
    })
  ] : [])
];
```

---

### Phase 4.5: UI 컴포넌트 및 필터 (3-4일)

#### 5.1 토글 컴포넌트
**파일**: `components/GeofenceToggle.tsx`
```typescript
import { useLogisticsStore } from '../store/useLogisticsStore';

export function GeofenceToggle() {
  const { showGeofences, toggleGeofences } = useLogisticsStore();

  return (
    <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <input
        type="checkbox"
        checked={showGeofences}
        onChange={toggleGeofences}
      />
      <span>지오펜스 표시</span>
    </label>
  );
}
```

#### 5.2 타임라인 컴포넌트
**파일**: `components/Timeline.tsx`
```typescript
import { FixedSizeList as List } from 'react-window';
import { useLogisticsStore } from '../store/useLogisticsStore';

export function Timeline() {
  const { annotatedEvents, filterDateRange } = useLogisticsStore();

  const filteredEvents = useMemo(() => {
    let events = annotatedEvents;

    if (filterDateRange.start) {
      events = events.filter(e => new Date(e.ts) >= filterDateRange.start!);
    }
    if (filterDateRange.end) {
      events = events.filter(e => new Date(e.ts) <= filterDateRange.end!);
    }

    return events.sort((a, b) =>
      new Date(b.ts).getTime() - new Date(a.ts).getTime()
    );
  }, [annotatedEvents, filterDateRange]);

  const Row = ({ index, style }: any) => {
    const event = filteredEvents[index];
    return (
      <div style={style} className="timeline-row">
        <span>{new Date(event.ts).toLocaleString()}</span>
        <span>{event.shpt_no}</span>
        <span>{event.status}</span>
        {event.zone && <span>{event.zone}</span>}
      </div>
    );
  };

  return (
    <div className="timeline-container">
      <List
        height={400}
        itemCount={filteredEvents.length}
        itemSize={40}
        width="100%"
      >
        {Row}
      </List>
    </div>
  );
}
```

---

## 성능 최적화 전략

### 1. 배치 처리
```typescript
// WebSocket 메시지 배치 처리 (500ms)
const batchQueue = useRef<Event[]>([]);
const batchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

const handleWebSocketEvent = useCallback((event: Event) => {
  batchQueue.current.push(event);

  if (!batchTimer.current) {
    batchTimer.current = setTimeout(() => {
      const batch = batchQueue.current.splice(0);
      useLogisticsStore.getState().addEvents(batch); // Batch update
      batchTimer.current = null;
    }, 500);
  }
}, []);
```

### 2. WebGL 최적화
```typescript
const layers = useMemo(() => [
  // ... layers
], [/* specific dependencies only */]);

<DeckGL
  layers={layers}
  updateTriggers={{
    'heatmap': [heatmapData.length], // Only update when data changes
    'geofences': [geofences],
    'eta-cones': [etaCones.length]
  }}
/>
```

### 3. 메모리 관리
```typescript
// Sliding window: Keep only last N events
const MAX_EVENTS = 1000;
const addEvent = (event: Event) => {
  const events = [...get().events, event].slice(-MAX_EVENTS);
  set({ events });
};
```

---

## 테스트 계획

### 1. 단위 테스트
- `utils/geofence.ts`: 포인트-다각형 검사 정확도
- `utils/heatmap.ts`: 집계 로직 정확성
- `utils/eta.ts`: ETA 계산 정확도

### 2. 통합 테스트
- WebSocket → Store → 렌더링 파이프라인
- 지오펜스 필터링 → 히트맵 업데이트
- ETA Cone → 클릭 인터랙션

### 3. 성능 테스트
- 1000+ 이벤트 처리 시간
- 히트맵 렌더링 FPS
- 메모리 사용량 모니터링

---

## 알려진 제한사항 및 리스크

### 1. 브라우저 호환성
- HeatmapLayer GPU 집계: iOS Safari 제한 가능
- WebGL 2.0 지원 필요
- 대용량 데이터 처리 성능 저하

### 2. 데이터 보안
- 클라이언트 노출: 민감한 BL 정보 최소화
- WSS 필수 (프로덕션)
- 데이터 검증 필요 (서버 측)

### 3. 성능 리스크
- 대량 이벤트(>5000) 처리 시 브라우저 성능 저하
- 히트맵 집계 계산 비용
- 메모리 누수 가능성

---

## 마이그레이션 전략

### 현재 → Client-Only 전환 체크리스트
- [ ] 의존성 설치 (@turf, aggregation-layers, mesh-layers, zustand)
- [ ] GeoJSON 데이터 준비 (`public/data/geofence.json`)
- [ ] Zustand Store 구현
- [ ] 지오펜스 판정 로직 구현
- [ ] 히트맵 집계 로직 구현
- [ ] ETA Cone 계산 로직 구현
- [ ] UI 컴포넌트 (토글, 타임라인, 필터) 구현
- [ ] 성능 최적화 적용
- [ ] 테스트 작성 및 검증

---

**문서 버전**: 1.0
**최종 업데이트**: 2026-01-10
```

---

## 요약 및 권장사항

### 즉시 시작 가능한 작업
1. 의존성 설치: 필요한 패키지 추가
2. GeoJSON 데이터 준비: `public/data/geofence.json` 생성
3. Zustand Store 기본 구조: 상태 관리 마이그레이션

### 주의사항
1. Pages Router vs App Router: 현재 Pages Router 사용 중이므로 App Router 전환은 선택
2. 점진적 마이그레이션: 기존 코드를 한 번에 교체하지 말고 단계적으로 추가
3. 성능 모니터링: 대량 데이터 처리 시 브라우저 성능 지속 관찰

### 다음 단계
Ask Mode에서는 파일 수정이 불가합니다. Agent Mode로 전환하거나, 위 마크다운을 복사해 `docs/Client-Only_Implementation_Plan.md`로 저장한 뒤 진행하세요.

이 계획을 문서로 저장할까요, 아니면 특정 단계부터 구현을 시작할까요?
