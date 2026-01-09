
# MOSB Logistics Dashboard - 구현 진행 상황 및 가이드

**작성일**: 2026-01-08
**프로젝트**: MOSB Logistics Live Map MVP v2
**스택**: Next.js 14 + React 18 + Deck.gl 9 + MapLibre 4 + FastAPI + WebSocket

---

## 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [Phase 1 구현 완료](#phase-1-구현-완료)
3. [Phase 2 구현 완료](#phase-2-구현-완료)
4. [Phase 3 계획 수립](#phase-3-계획-수립)
5. [Phase 3.1 구현 완료](#phase-31-구현-완료)
6. [Phase 3.1 로컬 검증 결과](#phase-31-로컬-검증-결과)
7. [Phase 3.2 구현 완료](#phase-32-구현-완료)
8. [Phase 3.2 테스트 검증 결과](#phase-32-테스트-검증-결과)
9. [Phase 3.1 상세 구현 가이드](#phase-31-상세-구현-가이드)
10. [참고 자료](#참고-자료)

---

## 프로젝트 개요

### 기술 스택

- **Frontend**: Next.js 14, React 18, Deck.gl 9, MapLibre 4
- **Backend**: FastAPI, WebSocket
- **데이터**: DuckDB with CSV fallback (Phase 3.1 완료)
- **인증**: JWT + RBAC (Phase 3.2 완료)
- **캐싱**: TTLCache (5min locations/shipments/legs, 1min events)
- **스타일**: 다크 테마

### 현재 데이터 구조

- **Locations**: 8개 (MOSB, WH, SITE×4, PORT, BERTH)
- **Shipments**: 2개 (AGI, DAS)
- **Legs**: 6개 (ROAD/SEA 구간)
- **Events**: 6개 (원래 3개 + demo 3개)

### 프로젝트 구조

```
mosb_logistics_dashboard_next_fastapi_mvp/
├── frontend/
│   ├── types/
│   │   └── logistics.ts          # 도메인 타입 정의
│   ├── lib/
│   │   ├── api.ts                # API 클라이언트 (인증 헤더 포함)
│   │   └── auth.ts               # 인증 서비스 (Phase 3.2)
│   ├── components/
│   │   └── Login.tsx             # 로그인 UI (Phase 3.2)
│   ├── hooks/
│   │   └── useWebSocket.ts       # WebSocket Hook
│   └── pages/
│       └── index.tsx              # 메인 페이지 (인증 통합)
└── backend/
    ├── auth.py                    # JWT 인증 (Phase 3.2)
    ├── rbac.py                    # 역할 기반 접근 제어 (Phase 3.2)
    ├── db.py                      # DuckDB 통합 (Phase 3.1)
    ├── cache.py                   # 캐싱 레이어 (Phase 3.1)
    ├── models.py                  # Pydantic 모델
    ├── main.py                    # FastAPI 앱
    ├── tests/
    │   ├── conftest.py            # pytest 설정 (Phase 3.2)
    │   ├── test_main.py           # API 테스트
    │   ├── test_auth.py           # 인증 테스트 (Phase 3.2)
    │   ├── test_db.py             # DB 테스트 (Phase 3.1)
    │   └── test_cache.py          # 캐시 테스트 (Phase 3.1)
    └── data/
        ├── logistics.db           # DuckDB 파일 (Phase 3.1)
        ├── locations.csv
        ├── shipments.csv
        ├── legs.csv
        └── events.csv
```

---

## Phase 1 구현 완료

**기간**: 1-2일
**상태**: ✅ 완료

### 구현 내용

#### 1. Frontend 타입 정의 (`frontend/types/logistics.ts`)

```typescript
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
  planned_etd: string;
  planned_eta: string;
}

export interface Event {
  event_id: string;
  ts: string;
  shpt_no: string;
  status: ShipmentStatus;
  location_id: string;
  lat: number;
  lon: number;
  remark: string;
}
```

#### 2. API 클라이언트 분리 (`frontend/lib/api.ts`)

- 중앙화된 API 접근
- 에러 처리 포함
- 모든 엔드포인트 메서드 구현

#### 3. WebSocket Hook (`frontend/hooks/useWebSocket.ts`)

- 자동 재연결 로직
- 백오프 전략
- 안전한 메시지 파싱 (UI 크래시 방지)
- 최대 재연결 시도 제한

#### 4. Backend 에러 처리 강화 (`backend/main.py`)

- 전역 예외 핸들러
- 구조화된 HTTPException 매핑
- 환경 변수 기반 CORS 설정
- 로깅 시스템

### 변경 파일

- `frontend/types/logistics.ts` (신규)
- `frontend/lib/api.ts` (신규)
- `frontend/hooks/useWebSocket.ts` (신규)
- `frontend/pages/index.tsx` (리팩토링)
- `backend/main.py` (에러 처리 추가)

---

## Phase 2 구현 완료

**기간**: 1주
**상태**: ✅ 완료

### 구현 내용

#### 1. Backend Pydantic 모델 (`backend/models.py`)

```python
class Location(BaseModel):
    location_id: str
    type: Literal["MOSB", "SITE", "WH", "PORT", "BERTH"]
    name: str
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)

class Shipment(BaseModel):
    shpt_no: str
    bl_no: str
    incoterm: str
    hs_code: str
    priority: Literal["HIGH", "MED", "LOW"]
    vendor: str

class Leg(BaseModel):
    leg_id: str
    shpt_no: str
    from_location_id: str
    to_location_id: str
    mode: Literal["ROAD", "SEA", "AIR"]
    planned_etd: str
    planned_eta: str

class EventCreate(BaseModel):
    shpt_no: str
    status: Literal["PLANNED", "IN_TRANSIT", "ARRIVED", "DELAYED", "HOLD"]
    location_id: str
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    remark: str = ""

class Event(EventCreate):
    event_id: str
    ts: str
```

#### 2. 테스트 코드 (`backend/tests/test_main.py`)

- 6개 테스트 케이스 구현
- 모든 API 엔드포인트 테스트
- 필터링 및 데모 이벤트 테스트

#### 3. 환경 변수 템플릿

- `backend/.env.example`
- `frontend/.env.local.example`

#### 4. 의존성 확장

**backend/requirements.txt**:
```
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.24.0
```

**frontend/package.json**:
- `lint`, `type-check` 스크립트 추가
- devDependencies 추가 (@types/node, @types/react, eslint 등)

#### 5. main.py 모델 통합

- `response_model` 적용
- `parse_rows` 함수로 안전한 파싱
- `WS_PING_INTERVAL` 환경 변수 적용

### 변경 파일

- `backend/models.py` (신규)
- `backend/tests/test_main.py` (신규)
- `backend/requirements.txt` (확장)
- `frontend/package.json` (스크립트 추가)
- `backend/main.py` (모델 통합)
- `backend/.env.example` (신규)
- `frontend/.env.local.example` (신규)

---

## Phase 3 계획 수립

**기간**: 2-4주
**상태**: 📋 계획 완료, 구현 대기

### Phase 3 구성

| 항목 | 목표 | 예상 시간 | 상태 |
|------|------|----------|------|
| 3.1 DB 준비 + 캐싱 | DuckDB 통합, 캐싱 레이어 | 1주 | ✅ 완료 |
| 3.2 인증/인가 | JWT + RBAC | 1주 | ✅ 완료 |
| 3.3 성능 최적화 | 서버/클라이언트 캐싱, React 최적화 | 3-5일 | 📋 대기 |
| 3.4 CI/CD 파이프라인 | GitHub Actions, Pre-commit | 3-5일 | 📋 대기 |

### Phase 3.1: DB 준비 + 캐싱

#### 목표
- CSV에서 DuckDB로 마이그레이션
- 캐싱 레이어 추가
- 기존 API 호환성 유지

#### 데이터베이스 선택: DuckDB (MVP 권장)

**장점**:
- 파일 기반, 설치 불필요
- CSV 임포트 간단
- SQL 쿼리 지원
- 빠른 분석 쿼리

**단점**:
- 동시 쓰기 제한
- 프로덕션 확장성 제한

#### 구현 계획

1. **DuckDB 통합** (1-2일)
   - `backend/db.py` 생성
   - 스키마 초기화
   - CSV 데이터 자동 로드

2. **캐싱 레이어** (1일)
   - `backend/cache.py` 생성
   - TTLCache 사용
   - 캐시 무효화 로직

3. **main.py 통합** (1일)
   - DB 인스턴스 생성
   - 캐시 적용
   - 기존 API 호환성 유지

4. **테스트 추가** (1일)
   - DB 테스트
   - 캐시 테스트

### Phase 3.2: 인증/인가 (JWT) + RBAC

#### 목표
- JWT 기반 인증
- 역할 기반 접근 제어 (Ops/Finance/Compliance/Admin)
- 보호된 엔드포인트

#### 구현 계획

1. **JWT 인증** (2일)
   - `backend/auth.py` 생성
   - 로그인 엔드포인트
   - 토큰 검증

2. **RBAC 데코레이터** (1일)
   - `backend/rbac.py` 생성
   - 역할 기반 접근 제어

3. **Frontend 통합** (2일)
   - `frontend/lib/auth.ts` 생성
   - API 클라이언트에 인증 헤더 추가
   - 로그인 UI (선택)

### Phase 3.3: 성능 최적화

#### 목표
- 서버 캐싱 최적화
- 클라이언트 메모이제이션
- React 최적화

#### 구현 계획

1. **서버 캐싱 개선** (1일)
   - 데코레이터 기반 캐싱
   - 캐시 키 생성 최적화

2. **클라이언트 메모이제이션** (1일)
   - `frontend/hooks/useMemoizedData.ts` 생성
   - 클라이언트 캐시 관리

3. **React 최적화** (1일)
   - `memo` 사용
   - `useMemo` 최적화

### Phase 3.4: CI/CD 파이프라인

#### 목표
- GitHub Actions 워크플로우
- 자동 테스트 실행
- Pre-commit 훅

#### 구현 계획

1. **GitHub Actions** (2일)
   - Backend 테스트 워크플로우
   - Frontend 빌드 워크플로우
   - 커버리지 리포트

2. **Pre-commit 훅** (1일)
   - Black 포맷팅
   - Ruff 린팅
   - 테스트 실행

---

## Phase 3.1 구현 완료

**기간**: 1주
**상태**: ✅ 완료 (2026-01-08)

### 구현 내용

#### 1. DuckDB 통합 (`backend/db.py`)

**주요 기능**:
- 스키마 자동 초기화 (locations, shipments, legs, events)
- CSV 자동 로드 (`read_csv` with `all_varchar=true`, `strict_mode=false`)
- 환경 변수 기반 DB 경로 설정 (`LOGISTICS_DB_PATH`)
- 메모리 DB 지원 (테스트용 `:memory:`)

**특징**:
- CSV 데이터가 없어도 동작 (빈 테이블로 시작)
- 타입 안전한 모델 변환 (`_fetch_models` 헬퍼)
- 이벤트 필터링 지원 (`since` 파라미터)
- CSV fallback 유지 (하위 호환성)

#### 2. 캐싱 레이어 (`backend/cache.py`)

**주요 기능**:
- TTLCache 기반 캐싱
  - Locations/Shipments/Legs: 5분 TTL
  - Events: 1분 TTL
- 개별 캐시 무효화 메서드
- `cache_response` 데코레이터 (async/sync 자동 감지)

**특징**:
- 캐시 키는 함수명 + 인자 기반 MD5 해시
- 동기/비동기 함수 모두 지원
- 캐시 무효화 API 제공

#### 3. main.py 통합

**변경사항**:
- DB 인스턴스 전역 생성
- 캐시 매니저 전역 생성
- 모든 엔드포인트에 DB + 캐시 적용
- CSV fallback 유지 (DB 로드 실패 시)

**이벤트 처리**:
- Demo 이벤트: DB 저장 → 캐시 무효화 → CSV append (하위 호환성)

#### 4. 테스트 커버리지

**test_db.py**:
- DB 연결 테스트
- Location 조회 테스트
- Events 필터링 테스트 (`since` 파라미터)
- Event 추가 테스트

**test_cache.py**:
- 캐시 히트/미스 테스트
- TTL 만료 테스트
- 캐시 무효화 테스트

### 변경 파일

- `backend/db.py` (신규, 201줄)
- `backend/cache.py` (신규, 93줄)
- `backend/main.py` (수정, +67/-18)
- `backend/tests/test_db.py` (신규, 63줄)
- `backend/tests/test_cache.py` (신규, 35줄)
- `backend/requirements.txt` (+2: duckdb, cachetools)
- `backend/.env.example` (+1: LOGISTICS_DB_PATH)
- `docs/AGENTS.md` (업데이트)

### 환경 변수 추가

```bash
# backend/.env.example
LOGISTICS_DB_PATH=./data/logistics.db  # Optional, defaults to data/logistics.db
```

---

## Phase 3.1 로컬 검증 결과

**검증 일시**: 2026-01-08
**검증 환경**: Windows, Python 3.13, FastAPI 0.119.0

### 검증 항목 및 결과

#### 1. 의존성 확인 ✅

```
duckdb: 1.3.2
cachetools: 5.5.0
fastapi: 0.119.0
```

#### 2. API 서버 실행 ✅

- 서버가 `http://localhost:8000`에서 정상 실행
- 모든 엔드포인트 정상 응답

#### 3. DB 파일 생성 확인 ✅

- `data/logistics.db` 파일 생성 확인
- 파일 크기: 12,288 bytes

#### 4. API 엔드포인트 테스트 ✅

| 엔드포인트 | 예상 | 실제 | 상태 |
|-----------|------|------|------|
| `/api/locations` | 8개 | 8개 | ✅ |
| `/api/shipments` | 2개 | 2개 | ✅ |
| `/api/legs` | 6개 | 6개 | ✅ |
| `/api/events` | 3+개 | 5개 | ✅ |

**응답 예시** (`/api/locations`):
```json
[
  {
    "location_id": "MOSB_ESNAAD",
    "type": "MOSB",
    "name": "MOSB - Samsung HVDC Lightning Project Esnaad",
    "lat": 24.328853,
    "lon": 54.45857
  },
  ...
]
```

#### 5. 캐시 동작 확인 ✅

**성능 측정 결과**:
- 첫 번째 요청 (캐시 미스): 4117ms
- 두 번째 요청 (캐시 히트): 2049ms
- **캐시 효과**: 약 2배 빠름 ✅

#### 6. 이벤트 생성 및 저장 확인 ✅

**Demo 이벤트 생성**:
- Event ID: `EV-6f7bfa4c`
- Status: `IN_TRANSIT`
- Shipment: `SHPT-AGI-0001`

**저장 확인**:
- ✅ DB에 저장됨
- ✅ CSV 파일에 추가됨:
  ```
  EV-6f7bfa4c,2026-01-08T19:48:00+00:00,SHPT-AGI-0001,IN_TRANSIT,MOSB_ESNAAD,24.328853,54.45857,Demo tick
  ```

### 검증 체크리스트

- [x] API 서버 정상 실행
- [x] DB 파일 생성 확인
- [x] Locations 엔드포인트 (8개)
- [x] Shipments 엔드포인트 (2개)
- [x] Legs 엔드포인트 (6개)
- [x] Events 엔드포인트 (5개)
- [x] 캐시 동작 확인 (약 2배 빠름)
- [x] Demo 이벤트 생성 성공
- [x] CSV 파일에 이벤트 추가 확인

### 알려진 이슈

#### DuckDB 파일 직접 접근 오류

**증상**: Python 스크립트로 DuckDB 파일 직접 접근 시 `UnicodeDecodeError` 발생

**원인**:
- 파일이 이미 열려있거나 잠겨있을 수 있음
- 경로 인코딩 문제 가능성

**영향**:
- API를 통한 접근은 정상 동작
- 직접 파일 접근만 제한됨

**해결책**:
- API 서버를 통한 접근 사용 (권장)
- 또는 API 서버 종료 후 파일 접근

### 검증 명령어

```bash
# API 서버 실행
cd mosb_logistics_dashboard_next_fastapi_mvp/backend
uvicorn main:app --reload --port 8000

# 엔드포인트 테스트
curl http://localhost:8000/api/locations
curl http://localhost:8000/api/shipments
curl http://localhost:8000/api/legs
curl http://localhost:8000/api/events

# Demo 이벤트 생성
curl -X POST http://localhost:8000/api/events/demo

# 캐시 성능 테스트
# 첫 번째 요청 후 두 번째 요청이 더 빠른지 확인
```

### 결론

**Phase 3.1 구현이 정상적으로 완료되었습니다**:
- ✅ DuckDB 통합 완료
- ✅ 캐싱 레이어 동작 확인
- ✅ CSV fallback 유지
- ✅ 이벤트 생성 및 저장 정상
- ✅ 모든 API 엔드포인트 정상 동작
- ✅ 캐시 성능 개선 확인 (약 2배)

---

## Phase 3.2 구현 완료

**기간**: 1주
**상태**: ✅ 완료 (2026-01-08)

### 구현 내용

#### 1. Backend JWT 인증 (`backend/auth.py`)

**주요 기능**:
- JWT 토큰 생성/검증 (python-jose)
- 비밀번호 해싱 (passlib + bcrypt)
- 사용자 인증 로직
- 4개 데모 사용자 제공

**데모 사용자**:
- `ops_user / ops123` (OPS)
- `finance_user / finance123` (FINANCE)
- `compliance_user / compliance123` (COMPLIANCE)
- `admin / admin123` (ADMIN)

**주요 함수**:
- `create_access_token()`: JWT 토큰 생성
- `get_current_user()`: 토큰 검증 및 사용자 정보 반환
- `authenticate_user()`: 사용자 인증

#### 2. RBAC 데코레이터 (`backend/rbac.py`)

**주요 기능**:
- 역할 기반 접근 제어
- `require_role()` 함수로 엔드포인트 보호
- 일관된 권한 검사

**사용 예시**:
```python
@app.get("/api/shipments")
@require_role(["OPS", "FINANCE", "ADMIN"])
async def get_shipments(current_user: User = Depends(get_current_user)):
    ...
```

#### 3. Backend 엔드포인트 통합

**인증 엔드포인트**:
- `POST /api/auth/login`: 로그인 및 토큰 발급
- `GET /api/auth/me`: 현재 사용자 정보

**보호된 데이터 엔드포인트**:
- `/api/locations`: 인증 필요 (모든 역할)
- `/api/shipments`: OPS, FINANCE, ADMIN만 접근 가능
- `/api/legs`: 인증 필요 (모든 역할)
- `/api/events`: 인증 필요 (모든 역할)
- `/api/events/demo`: OPS, ADMIN만 접근 가능

#### 4. Frontend 인증 서비스 (`frontend/lib/auth.ts`)

**주요 기능**:
- 로그인/로그아웃
- 토큰 관리 (localStorage)
- 사용자 정보 캐싱
- 역할 체크 헬퍼 (`hasRole`, `hasAnyRole`)
- 브라우저 환경 체크 (SSR 호환)

#### 5. Frontend 로그인 UI (`frontend/components/Login.tsx`)

**특징**:
- 다크 테마 디자인
- 에러 처리
- 로딩 상태 표시
- 데모 사용자 안내

#### 6. API 클라이언트 업데이트 (`frontend/lib/api.ts`)

**변경사항**:
- 모든 요청에 `Authorization: Bearer <token>` 헤더 추가
- 401 에러 시 자동 로그아웃
- 403 에러 처리 (권한 부족)

#### 7. 메인 페이지 통합 (`frontend/pages/index.tsx`)

**변경사항**:
- 로그인 상태 확인
- 미인증 시 로그인 화면 표시
- 역할 기반 UI 제어 (예: Demo 이벤트 버튼)

### 역할별 접근 권한

| 역할 | Locations | Shipments | Legs | Events | Demo Event |
|------|-----------|-----------|------|--------|------------|
| OPS | ✅ | ✅ | ✅ | ✅ | ✅ |
| FINANCE | ✅ | ✅ | ✅ | ✅ | ❌ |
| COMPLIANCE | ✅ | ❌ | ✅ | ✅ | ❌ |
| ADMIN | ✅ | ✅ | ✅ | ✅ | ✅ |

### 변경 파일

- `backend/auth.py` (신규, 133줄)
- `backend/rbac.py` (신규, 26줄)
- `backend/main.py` (수정, +33/-6)
- `backend/tests/test_auth.py` (신규, 79줄)
- `backend/tests/test_main.py` (수정, +38/-6)
- `backend/tests/conftest.py` (신규, pytest 설정)
- `backend/requirements.txt` (+3: python-jose, passlib, python-multipart)
- `backend/.env.example` (+3: JWT 관련 환경 변수)
- `frontend/lib/auth.ts` (신규, 108줄)
- `frontend/lib/api.ts` (수정, +60/-10)
- `frontend/components/Login.tsx` (신규, 113줄)
- `frontend/pages/index.tsx` (수정, +106/-4)
- `docs/AGENTS.md` (업데이트)

### 환경 변수 추가

```bash
# backend/.env.example
JWT_SECRET_KEY=your-secret-key-change-in-prod
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 알려진 제한사항

- **WebSocket 인증 미구현**: 현재 WebSocket은 인증 없이 접근 가능
  - 향후 개선: 토큰 쿼리 파라미터 또는 subprotocol 검증 추가

---

## Phase 3.2 테스트 검증 결과

**검증 일시**: 2026-01-08
**검증 환경**: Windows, Python 3.13

### 테스트 실행 결과

#### 전체 테스트 통과 ✅

```
20 tests passed
```

#### 테스트 구성

**인증 테스트** (`test_auth.py`):
- ✅ `test_login_success`: 로그인 성공
- ✅ `test_login_failure`: 로그인 실패 처리
- ✅ `test_get_me_with_token`: 토큰으로 사용자 정보 조회
- ✅ `test_protected_endpoint_without_token`: 토큰 없이 접근 거부
- ✅ `test_protected_endpoint_with_token`: 토큰으로 접근 허용
- ✅ `test_rbac_access_denied`: 권한 없는 역할 접근 거부

**API 테스트** (`test_main.py`):
- ✅ `test_get_locations`: Locations 엔드포인트
- ✅ `test_get_shipments`: Shipments 엔드포인트
- ✅ `test_get_legs`: Legs 엔드포인트
- ✅ `test_get_events`: Events 엔드포인트
- ✅ `test_get_events_with_since`: Events 필터링
- ✅ `test_post_demo_event`: Demo 이벤트 생성

**DB 테스트** (`test_db.py`):
- ✅ `test_db_connection`: DB 연결
- ✅ `test_db_get_locations`: Location 조회
- ✅ `test_db_get_events_with_since`: Events 필터링
- ✅ `test_db_append_event`: Event 추가

**캐시 테스트** (`test_cache.py`):
- ✅ `test_cache_hit`: 캐시 히트
- ✅ `test_cache_miss`: 캐시 미스
- ✅ `test_cache_ttl`: TTL 만료
- ✅ `test_cache_invalidation`: 캐시 무효화

### 개선 사항 적용

#### 1. DeprecationWarning 제거 ✅

**변경사항**:
- `auth.py`의 `datetime.utcnow()` → `datetime.now(timezone.utc)` 변경
- `timezone` import 추가

**결과**:
- DeprecationWarning 없음
- 미래 Python 버전 호환성 확보

#### 2. pytest import 문제 해결 ✅

**변경사항**:
- `backend/tests/conftest.py` 추가
- Backend 디렉토리를 Python 경로에 자동 추가

**결과**:
- PYTHONPATH 설정 없이 테스트 실행 가능
- `pytest -q` 명령어만으로 실행 가능

### 검증 체크리스트

- [x] JWT 인증 구현
- [x] RBAC 데코레이터 구현
- [x] 로그인 엔드포인트 동작
- [x] 보호된 엔드포인트 동작
- [x] RBAC 동작 확인
- [x] Frontend 인증 통합
- [x] 로그인 UI 구현
- [x] 테스트 코드 작성
- [x] 모든 테스트 통과 (20개)
- [x] DeprecationWarning 제거
- [x] pytest import 문제 해결

---

## Phase 3.1 상세 구현 가이드

### Step 1: 의존성 추가

```txt
# backend/requirements.txt에 추가
duckdb>=0.9.0
cachetools>=5.3.0
```

### Step 2: 데이터베이스 모듈 생성

**파일**: `backend/db.py`

주요 기능:
- DuckDB 연결 관리
- 스키마 초기화
- CSV 데이터 자동 로드
- CRUD 메서드

### Step 3: 캐싱 모듈 생성

**파일**: `backend/cache.py`

주요 기능:
- TTLCache 관리
- 캐시 히트/미스 처리
- 캐시 무효화

### Step 4: main.py 통합

주요 변경사항:
- DB 인스턴스 생성
- 캐시 매니저 생성
- 엔드포인트에 캐싱 적용
- 이벤트 추가 시 캐시 무효화

### Step 5: 테스트 추가

**파일**:
- `backend/tests/test_db.py`
- `backend/tests/test_cache.py`

### 실행 순서

1. 의존성 설치: `pip install -r requirements.txt`
2. 파일 생성: `db.py`, `cache.py`, 테스트 파일
3. `main.py` 수정
4. 테스트 실행: `pytest -q -v`
5. 수동 테스트: API 엔드포인트 확인

### 검증 체크리스트 (참고용)

- [x] `duckdb` 및 `cachetools` 설치 확인
- [x] `db.py` 모듈 생성 및 테스트 통과
- [x] `cache.py` 모듈 생성 및 테스트 통과
- [x] `main.py` 통합 후 기존 API 동작 확인
- [x] 캐시 동작 확인
- [x] DB에 데이터 저장 확인
- [x] 모든 테스트 통과

---

## 참고 자료

### 프로젝트 문서

- `docs/AGENTS.md` - 프로젝트 아키텍처 가이드
- `docs/constitution.md` - 프로젝트 규칙
- `mosb_logistics_dashboard_next_fastapi_mvp/README.txt` - 실행 가이드

### 주요 명령어

```bash
# Backend 실행
cd mosb_logistics_dashboard_next_fastapi_mvp/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Backend 테스트
pytest -q -v

# Frontend 실행
cd mosb_logistics_dashboard_next_fastapi_mvp/frontend
npm install
npm run dev

# Frontend 타입 체크
npm run type-check

# Frontend 린트
npm run lint
```

### 환경 변수

**Backend** (`.env`):
```
DATA_DIR=./data
LOGISTICS_DB_PATH=./data/logistics.db
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
WS_PING_INTERVAL=10
JWT_SECRET_KEY=your-secret-key-change-in-prod
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Frontend** (`.env.local`):
```
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_WS_RECONNECT_DELAY=3000
NEXT_PUBLIC_WS_MAX_RECONNECT_ATTEMPTS=10
```

---

## 다음 단계

1. **Phase 3.3 구현 시작** - 성능 최적화
2. **WebSocket 인증 추가** (선택) - 실시간 기능 보호
3. **Phase 3.4 준비** - CI/CD 파이프라인 설계

---

## 변경 이력

- **2026-01-08**: Phase 1, 2 구현 완료 문서화
- **2026-01-08**: Phase 3 계획 수립
- **2026-01-08**: Phase 3.1 상세 구현 가이드 작성
- **2026-01-08**: Phase 3.1 구현 완료 및 로컬 검증 결과 추가
- **2026-01-08**: Phase 3.2 구현 완료 및 테스트 검증 결과 추가
- **2026-01-08**: DeprecationWarning 제거 및 pytest 설정 개선

---

**문서 버전**: 1.2
**최종 업데이트**: 2026-01-08
```

이 문서를 `docs/Implementation_Progress.md`에 저장하세요.

현재 "ask mode"이므로 파일 생성이 필요하면 "agent mode"로 전환하거나, 위 마크다운을 복사해 직접 저장하세요.

문서 위치: `docs/Implementation_Progress.md`

추가로 필요한 내용이 있으면 알려주세요.
