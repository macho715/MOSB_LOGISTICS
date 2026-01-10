# AGENTS.md — MOSB Logistics Sleek Ops Dashboard (Next.js + Deck.gl + FastAPI + WS)

You are an AI coding agent working in this repository. Follow this file **strictly**.  
If this doc conflicts with repo reality (package.json/pyproject/docker-compose), **repo wins** and you must update this file to match.

---

## 0) Executive Summary

- 목표: Streamlit보다 기능 많고 세련된 **현장 물류 Ops Dashboard** 구축(멀티페이지/권한/RBAC/실시간/지도 커스텀 레이어).
- 권장 스택: **Next.js 16.1.1 + React 18 + Deck.gl 9 + MapLibre 4 + FastAPI + WebSocket**.
- 확장성: Port/Berth, Geofence, Heatmap, ETA cone, 이벤트 스트림, 감사로그까지 자연 확장.

EN: For a polished, feature-rich ops dashboard, standardize on **Next.js + Deck.gl + FastAPI + WebSocket**.

---

## 1) Repository Reality Snapshot (Known)

Based on current structure review:

- Frontend: **Next.js 16.1.1, React 18, Deck.gl 9, MapLibre 4**
- Backend: **FastAPI + WebSocket**
- Data: **CSV seeds + DuckDB**
- UI: **Dark theme**
- Current data:
  - Locations: **8** (MOSB, WH, SITE×4, PORT, BERTH)
  - Shipments: **2** (AGI, DAS)
  - Legs: **6** (ROAD/SEA)
  - Events: **3** (demo)

If any of the above differs in repo, update this section immediately.

---

## 2) Platform Selection Matrix (Reference)

| Platform                        | UI polish | Realtime (WS) | Map/layers extensibility | Ops/RBAC | Build speed |
| ------------------------------- | --------: | ------------: | -----------------------: | -------: | ----------: |
| **Next.js + Deck.gl + FastAPI** | Highest   | Highest       | Highest                  | High\*   | Medium      |
| Dash(Plotly)                    | Med–High  | Medium        | High                     | Medium   | Medium      |
| Grafana/Superset + Map          | Medium    | Medium        | Medium                   | High     | Fast        |

\* RBAC requires implementation (but architecture supports it cleanly).

---

## 3) System Architecture (Contract-first)

### 3.1 Services / Folders (Do not invent if repo differs)

- `mosb_logistics_dashboard_next_fastapi_mvp/frontend/`: Next.js UI
- `mosb_logistics_dashboard_next_fastapi_mvp/backend/`: FastAPI (REST + WS)
- `mosb_logistics_dashboard_next_fastapi_mvp/backend/data/`: CSV seeds (MVP)
- `infra/`: docker/compose/reverse proxy (optional)

### 3.2 Canonical Domain Types (Frontend)

Mandatory type file:

- `mosb_logistics_dashboard_next_fastapi_mvp/frontend/types/logistics.ts`

Use this canonical contract (keep backward compatible):

```ts
export type LocationType = "MOSB" | "SITE" | "WH" | "PORT" | "BERTH";
export type ShipmentStatus = "PLANNED" | "IN_TRANSIT" | "ARRIVED" | "DELAYED" | "HOLD";
export type TransportMode = "ROAD" | "SEA" | "AIR";

export interface Location {
  location_id: string;
  type: LocationType;
  name: string;
  lat: number;
  lon: number;
}

export interface Shipment {
  shpt_no: string;
  bl_no: string;
  incoterm: string;
  hs_code: string;
  priority: "HIGH" | "MED" | "LOW";
  vendor: string;
}

export interface Leg {
  leg_id: string;
  shpt_no: string;
  from_location_id: string;
  to_location_id: string;
  mode: TransportMode;
  planned_etd: string; // ISO8601
  planned_eta: string; // ISO8601
}

export interface Event {
  event_id: string;
  ts: string; // ISO8601
  shpt_no: string;
  status: ShipmentStatus;
  location_id: string;
  lat: number;
  lon: number;
  remark: string;
}
```

### 3.3 API Client Separation (Frontend)

Centralize API access:

- `mosb_logistics_dashboard_next_fastapi_mvp/frontend/lib/api.ts`

```ts
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
```

### 3.4 WebSocket Hook (Frontend)

Standard hook location:

- `mosb_logistics_dashboard_next_fastapi_mvp/frontend/hooks/useWebSocket.ts`

Rules:

- reconnect backoff
- max attempts
- ignore unknown message shapes
- parse errors must not crash UI

(Implementation may follow your reference snippet.)

### 3.5 Backend Validation (Pydantic)

Single source of truth models:

- `mosb_logistics_dashboard_next_fastapi_mvp/backend/models.py`

Minimum models:

- `Location`, `Shipment`, `Leg`, `EventCreate`, `Event`

Rules:

- lat/lon bounds
- enum literals for `type`, `mode`, `status`
- timestamps in ISO8601 string or `datetime` (pick one; keep consistent)

### 3.6 Backend Error Handling

Add:

- global exception handler
- structured HTTPException mapping
- CORS configuration using env (`CORS_ORIGINS`)

---

## 4) MVP Scope (Non-negotiable)

MVP must ship with:

- Map: MOSB 중심 + **8 locations** 표시(현재 데이터 기준)
- Legs: **6 legs** 시각화 (ROAD/SEA)
- KPI: Planned/InTransit/Arrived/Delayed/Total
- Event timeline/list + filters (shpt_no/status)
- WS wiring + demo event publish
- Data: CSV seed (DB/Sheets/Airtable은 다음 단계)

Assumption (must remain replaceable):

- 일부 SITE는 reference pin으로 시작 가능 → 운영 정밀 pin(Gate/Jetty/Helipad)로 교체 가능해야 함.

---

## 5) Build / Run (Do not guess; align to repo)

### 5.1 Frontend (Next.js)

- Install: `cd mosb_logistics_dashboard_next_fastapi_mvp/frontend && npm install` (or pnpm/yarn if repo uses it)
- Dev: `cd mosb_logistics_dashboard_next_fastapi_mvp/frontend && npm run dev`
- Lint: `cd mosb_logistics_dashboard_next_fastapi_mvp/frontend && npm run lint`
- Typecheck: `cd mosb_logistics_dashboard_next_fastapi_mvp/frontend && npm run type-check`

### 5.2 Backend (FastAPI)

- Install: `cd mosb_logistics_dashboard_next_fastapi_mvp/backend && pip install -r requirements.txt`
- Dev: `cd mosb_logistics_dashboard_next_fastapi_mvp/backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- Test: `cd mosb_logistics_dashboard_next_fastapi_mvp/backend && pytest -q`

If repo uses different commands/paths, update this section and keep one canonical set.

---

## 6) Environment Configuration (Required)

Provide examples (must exist in repo as templates).

### 6.1 Backend

- `mosb_logistics_dashboard_next_fastapi_mvp/backend/.env.example`

```bash
DATA_DIR=./data
LOGISTICS_DB_PATH=./data/logistics.db
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
WS_PING_INTERVAL=10
```

### 6.2 Frontend

- `mosb_logistics_dashboard_next_fastapi_mvp/frontend/.env.local.example`

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_WS_RECONNECT_DELAY=3000
NEXT_PUBLIC_WS_MAX_RECONNECT_ATTEMPTS=10
```

Rules:

- never commit `.env` with secrets
- only `NEXT_PUBLIC_*` for non-secret public values

---

## 7) Testing (TDD-first)

Backend minimal tests:

- `mosb_logistics_dashboard_next_fastapi_mvp/backend/tests/test_main.py`

Minimum:

- `/api/locations` returns list
- `/api/shipments` returns list
- `/api/events` returns list
- `/api/events?since=...` returns 200
- `POST /api/events/demo` returns `{ ok: true, event }` and known `shpt_no` for demo

Frontend tests are optional for MVP unless repo already has a framework configured.

---

## 8) Dependency Baseline (Reference Only)

### 8.1 Frontend package.json scripts (target)

```json
{
  "scripts": {
    "dev": "next dev -p 3000",
    "build": "next build",
    "start": "next start -p 3000",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  }
}
```

### 8.2 Backend requirements.txt (target)

```txt
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.24.0
```

If repo already pins versions differently, do not override silently—propose via PR.

---

## 9) Prioritized Execution Plan

### Phase 1 (1–2 days): immediate hardening

1) Frontend types file (`types/logistics.ts`)  
2) API client (`lib/api.ts`)  
3) WS hook with reconnect policy  
4) Backend basic error handler + CORS

### Phase 2 (1 week): reliability

1) Pydantic models + validation  
2) Backend tests + CI sanity (if CI exists)  
3) env templates + logging

### Phase 3 (2–4 weeks): scale

1) DB readiness (DuckDB/Postgres) + caching  
2) AuthN/AuthZ (JWT) + RBAC  
3) performance optimization (server cache, client memoization)  
4) CI/CD pipeline

---

## 10) Security / Ops Rules (Strict)

- No secrets in git (tokens, PAT, keys).
- No broad CORS in production (dev only; prod must be explicit origins).
- No breaking changes to API contracts without version bump.
- WS must not crash on malformed messages.

---

## 11) “Ask Mode” vs “Agent Mode” Rule

- In **Ask Mode**: provide designs, diffs, and exact file paths; do not modify code.
- In **Agent Mode**: you may implement changes, run checks, and propose PR-ready commits.

If asked to implement, switch to Agent Mode explicitly and follow:

- smallest diff
- tests updated
- commands run listed (actual, not hypothetical)

---

## 12) Command Recommendations (Ops)

- `/logi-master kpi-dash`
- `/switch_mode ORACLE + /logi-master predict`
- `/logi-master weather-tie`

Next expansion targets (once MVP stable):

1) `legs.csv` 기반 정확한 PathLayer  
2) Geofence 진입/이탈 이벤트  
3) Role-based RBAC (Ops/Finance/Compliance)

---
