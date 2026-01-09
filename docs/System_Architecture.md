# MOSB Logistics Dashboard - 시스템 아키텍처 문서

**작성일**: 2026-01-08
**프로젝트**: MOSB Logistics Live Map MVP v2
**버전**: 1.0

---

## 목차

1. [시스템 개요](#시스템-개요)
2. [아키텍처 다이어그램](#아키텍처-다이어그램)
3. [시스템 구성 요소](#시스템-구성-요소)
4. [데이터 흐름](#데이터-흐름)
5. [인증/인가 아키텍처](#인증인가-아키텍처)
6. [기술 스택](#기술-스택)
7. [배포 아키텍처](#배포-아키텍처)

---

## 시스템 개요

MOSB Logistics Dashboard는 실시간 물류 추적 및 운영 관리를 위한 웹 기반 대시보드입니다.

### 핵심 기능

- **실시간 지도 시각화**: Deck.gl + MapLibre 기반 지도 표시
- **물류 데이터 관리**: Locations, Shipments, Legs, Events 추적
- **실시간 이벤트 스트리밍**: WebSocket 기반 실시간 업데이트
- **역할 기반 접근 제어**: JWT + RBAC 기반 보안
- **성능 최적화**: 서버/클라이언트 캐싱

---

## 아키텍처 다이어그램

### 전체 시스템 아키텍처

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[웹 브라우저]
        UI[Next.js Frontend<br/>React 18 + Deck.gl]
    end

    subgraph "Frontend Components"
        Pages[Pages<br/>index.tsx]
        Components[Components<br/>Login.tsx]
        Hooks[Hooks<br/>useWebSocket.ts]
        Lib[Lib<br/>api.ts, auth.ts]
        Types[Types<br/>logistics.ts]
    end

    subgraph "API Layer"
        REST[REST API<br/>FastAPI]
        WS[WebSocket<br/>/ws/events]
    end

    subgraph "Backend Services"
        Auth[Auth Service<br/>JWT + RBAC]
        Cache[Cache Manager<br/>TTLCache]
        DB[Database Service<br/>DuckDB]
    end

    subgraph "Data Layer"
        DuckDB[(DuckDB<br/>logistics.db)]
        CSV[CSV Files<br/>Fallback]
    end

    Browser --> UI
    UI --> Pages
    Pages --> Components
    Pages --> Hooks
    Pages --> Lib
    Lib --> Types

    UI -->|HTTP + JWT| REST
    UI -->|WebSocket| WS

    REST --> Auth
    REST --> Cache
    REST --> DB
    WS --> DB

    DB --> DuckDB
    DB -.->|Fallback| CSV

    Cache -.->|Cache Hit| REST
    Cache -.->|Cache Miss| DB
```

### 컴포넌트 상호작용 다이어그램

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as Auth Service
    participant API as FastAPI
    participant C as Cache
    participant D as DuckDB
    participant WS as WebSocket

    U->>F: 접속
    F->>A: 로그인 요청
    A->>API: POST /api/auth/login
    API->>A: JWT 토큰 발급
    A->>F: 토큰 저장 (localStorage)

    F->>API: GET /api/locations (Bearer Token)
    API->>A: 토큰 검증
    A->>API: 사용자 정보 반환
    API->>C: 캐시 확인
    alt 캐시 히트
        C->>API: 캐시된 데이터
    else 캐시 미스
        API->>D: DB 쿼리
        D->>API: 데이터 반환
        API->>C: 캐시 저장
    end
    API->>F: JSON 응답

    F->>WS: WebSocket 연결
    WS->>F: 실시간 이벤트 스트리밍

    U->>F: Demo 이벤트 생성
    F->>API: POST /api/events/demo
    API->>D: 이벤트 저장
    API->>C: 캐시 무효화
    API->>WS: 브로드캐스트
    WS->>F: 실시간 업데이트
```

### 데이터 모델 관계도

```mermaid
erDiagram
    LOCATION ||--o{ LEG : "from"
    LOCATION ||--o{ LEG : "to"
    LOCATION ||--o{ EVENT : "occurs_at"
    SHIPMENT ||--o{ LEG : "has"
    SHIPMENT ||--o{ EVENT : "tracks"

    LOCATION {
        string location_id PK
        string type
        string name
        float lat
        float lon
    }

    SHIPMENT {
        string shpt_no PK
        string bl_no
        string incoterm
        string hs_code
        string priority
        string vendor
    }

    LEG {
        string leg_id PK
        string shpt_no FK
        string from_location_id FK
        string to_location_id FK
        string mode
        string planned_etd
        string planned_eta
    }

    EVENT {
        string event_id PK
        string ts
        string shpt_no FK
        string status
        string location_id FK
        float lat
        float lon
        string remark
    }
```

---

## 시스템 구성 요소

### Frontend (Next.js)

#### 1. 페이지 컴포넌트

**`pages/index.tsx`**
- 메인 대시보드 페이지
- 인증 상태 관리
- 지도 시각화 (Deck.gl)
- KPI 표시
- 이벤트 타임라인

#### 2. 컴포넌트

**`components/Login.tsx`**
- 로그인 폼
- 사용자 인증 UI
- 에러 처리

#### 3. 라이브러리

**`lib/api.ts`**
- REST API 클라이언트
- 인증 헤더 자동 추가
- 에러 처리

**`lib/auth.ts`**
- 인증 서비스
- 토큰 관리
- 사용자 정보 캐싱
- 역할 체크 헬퍼

#### 4. 훅

**`hooks/useWebSocket.ts`**
- WebSocket 연결 관리
- 자동 재연결
- 메시지 파싱

#### 5. 타입 정의

**`types/logistics.ts`**
- 도메인 타입 정의
- TypeScript 인터페이스

### Backend (FastAPI)

#### 1. 메인 애플리케이션

**`main.py`**
- FastAPI 앱 인스턴스
- 엔드포인트 정의
- 미들웨어 설정
- 예외 처리

#### 2. 인증/인가

**`auth.py`**
- JWT 토큰 생성/검증
- 비밀번호 해싱
- 사용자 인증
- 토큰 검증 의존성

**`rbac.py`**
- 역할 기반 접근 제어
- 권한 검사 데코레이터

#### 3. 데이터 계층

**`db.py`**
- DuckDB 연결 관리
- 스키마 초기화
- CSV 데이터 로드
- CRUD 작업

**`models.py`**
- Pydantic 모델 정의
- 데이터 검증

#### 4. 캐싱

**`cache.py`**
- TTLCache 관리
- 캐시 무효화
- 캐시 데코레이터

---

## 데이터 흐름

### 1. 로그인 플로우

```mermaid
flowchart TD
    Start([사용자 로그인]) --> Input[사용자명/비밀번호 입력]
    Input --> Frontend[Frontend: AuthService.login]
    Frontend --> API[POST /api/auth/login]
    API --> Auth[Auth: authenticate_user]
    Auth --> Check{인증 성공?}
    Check -->|실패| Error[401 Unauthorized]
    Check -->|성공| Token[토큰 생성]
    Token --> Response[토큰 반환]
    Response --> Store[localStorage 저장]
    Store --> End([로그인 완료])
    Error --> End
```

### 2. 데이터 조회 플로우

```mermaid
flowchart TD
    Start([API 요청]) --> AuthCheck{인증 확인}
    AuthCheck -->|실패| Unauthorized[401 Unauthorized]
    AuthCheck -->|성공| RoleCheck{권한 확인}
    RoleCheck -->|실패| Forbidden[403 Forbidden]
    RoleCheck -->|성공| CacheCheck{캐시 확인}
    CacheCheck -->|히트| CacheReturn[캐시 반환]
    CacheCheck -->|미스| DBQuery[DB 쿼리]
    DBQuery --> DBError{DB 오류?}
    DBError -->|있음| CSVFallback[CSV Fallback]
    DBError -->|없음| DBResult[DB 결과]
    CSVFallback --> Parse[데이터 파싱]
    DBResult --> Parse
    Parse --> Validate[Pydantic 검증]
    Validate --> CacheStore[캐시 저장]
    CacheStore --> Response[응답 반환]
    CacheReturn --> Response
    Response --> End([완료])
```

### 3. 실시간 이벤트 플로우

```mermaid
flowchart TD
    Start([이벤트 생성]) --> Create[POST /api/events/demo]
    Create --> Auth[인증 확인]
    Auth --> Role[권한 확인 OPS/ADMIN]
    Role --> Validate[이벤트 검증]
    Validate --> DBWrite[DB 저장]
    DBWrite --> CacheInvalidate[캐시 무효화]
    CacheInvalidate --> CSVAppend[CSV 추가]
    CSVAppend --> Broadcast[WebSocket 브로드캐스트]
    Broadcast --> Clients[연결된 클라이언트]
    Clients --> Update[실시간 UI 업데이트]
    Update --> End([완료])
```

---

## 인증/인가 아키텍처

### JWT 토큰 구조

```mermaid
graph LR
    Login[로그인 요청] --> Verify[비밀번호 검증]
    Verify --> Token[JWT 생성]
    Token --> Payload[Payload<br/>sub: username<br/>role: OPS/FINANCE/etc<br/>exp: timestamp]
    Payload --> Encode[HS256 서명]
    Encode --> Return[토큰 반환]
    Return --> Client[클라이언트 저장]
    Client --> Request[API 요청]
    Request --> Validate[토큰 검증]
    Validate --> Extract[사용자 정보 추출]
    Extract --> RBAC[RBAC 검사]
    RBAC --> Allow[접근 허용]
```

### 역할 기반 접근 제어 (RBAC)

```mermaid
graph TD
    Request[API 요청] --> Token[토큰 추출]
    Token --> Decode[JWT 디코딩]
    Decode --> User[사용자 정보]
    User --> Role[역할 확인]
    Role --> Check{엔드포인트 권한}

    Check -->|Locations| All[모든 역할 허용]
    Check -->|Shipments| OpsFinAdmin[OPS/FINANCE/ADMIN]
    Check -->|Legs| All2[모든 역할 허용]
    Check -->|Events| All3[모든 역할 허용]
    Check -->|Demo Event| OpsAdmin[OPS/ADMIN]

    OpsFinAdmin --> Allow[접근 허용]
    All --> Allow
    All2 --> Allow
    All3 --> Allow
    OpsAdmin --> Allow

    Check -->|권한 없음| Deny[403 Forbidden]
```

### 인증 미들웨어 체인

```mermaid
sequenceDiagram
    participant C as Client
    participant M as Middleware
    participant A as Auth
    participant R as RBAC
    participant E as Endpoint
    participant D as Database

    C->>M: HTTP Request + JWT
    M->>M: CORS 검사
    M->>A: 토큰 검증
    A->>A: JWT 디코딩
    A->>A: 사용자 조회
    A->>M: 사용자 정보
    M->>R: 역할 확인
    R->>R: 권한 검사
    alt 권한 있음
        R->>E: 요청 전달
        E->>D: 데이터 조회
        D->>E: 데이터 반환
        E->>M: 응답
        M->>C: JSON 응답
    else 권한 없음
        R->>M: 403 Forbidden
        M->>C: 에러 응답
    end
```

---

## 기술 스택

### Frontend

| 계층 | 기술 | 버전 | 용도 |
|------|------|------|------|
| Framework | Next.js | 14.2.0 | React 프레임워크 |
| UI Library | React | 18.2.0 | UI 컴포넌트 |
| Map Engine | Deck.gl | 9.0.0 | 지도 레이어 렌더링 |
| Map Provider | MapLibre | 4.0.0 | 지도 타일 제공 |
| Language | TypeScript | 5.0.0 | 타입 안전성 |

### Backend

| 계층 | 기술 | 버전 | 용도 |
|------|------|------|------|
| Framework | FastAPI | 0.119.0 | REST API 서버 |
| ASGI Server | Uvicorn | 0.30.0 | 비동기 서버 |
| Database | DuckDB | 1.3.2 | 데이터 저장 |
| Caching | cachetools | 5.5.0 | 메모리 캐싱 |
| Validation | Pydantic | 2.0.0 | 데이터 검증 |
| Auth | python-jose | 3.3.0 | JWT 처리 |
| Password | passlib | 1.7.4 | 비밀번호 해싱 |

### 인프라

| 항목 | 기술 | 용도 |
|------|------|------|
| 데이터 저장 | DuckDB + CSV | 파일 기반 DB |
| 실시간 통신 | WebSocket | 이벤트 스트리밍 |
| 배포 | (계획) | Docker, CI/CD |

---

## 배포 아키텍처

### 현재 구조 (개발 환경)

```mermaid
graph TB
    subgraph "Development"
        Dev[개발자 머신]
        FrontendDev[Frontend<br/>localhost:3000]
        BackendDev[Backend<br/>localhost:8000]
        LocalDB[(DuckDB<br/>로컬 파일)]
    end

    Dev --> FrontendDev
    Dev --> BackendDev
    BackendDev --> LocalDB
    FrontendDev -->|HTTP| BackendDev
    FrontendDev -->|WebSocket| BackendDev
```

### 프로덕션 구조 (계획)

```mermaid
graph TB
    subgraph "Client"
        Browser[웹 브라우저]
    end

    subgraph "CDN / Load Balancer"
        LB[로드 밸런서]
    end

    subgraph "Frontend Layer"
        Frontend1[Next.js App 1]
        Frontend2[Next.js App 2]
    end

    subgraph "API Gateway"
        Gateway[API Gateway<br/>인증/라우팅]
    end

    subgraph "Backend Layer"
        API1[FastAPI 1]
        API2[FastAPI 2]
    end

    subgraph "Data Layer"
        DB[(PostgreSQL<br/>또는 DuckDB)]
        Cache[Redis Cache]
    end

    Browser --> LB
    LB --> Frontend1
    LB --> Frontend2
    Frontend1 --> Gateway
    Frontend2 --> Gateway
    Gateway --> API1
    Gateway --> API2
    API1 --> Cache
    API2 --> Cache
    API1 --> DB
    API2 --> DB
    Cache -.->|Cache Miss| DB
```

---

## 보안 아키텍처

### 인증/인가 플로우

```mermaid
graph TB
    subgraph "Authentication"
        Login[로그인] --> Verify[비밀번호 검증]
        Verify --> JWT[JWT 토큰 발급]
    end

    subgraph "Authorization"
        Request[API 요청] --> Extract[토큰 추출]
        Extract --> Validate[토큰 검증]
        Validate --> User[사용자 정보]
        User --> Role[역할 확인]
        Role --> Permission[권한 검사]
    end

    subgraph "Data Access"
        Permission -->|허용| Access[데이터 접근]
        Permission -->|거부| Deny[403 Forbidden]
    end

    JWT --> Request
```

### 보안 계층

```mermaid
graph TD
    Client[클라이언트] --> HTTPS[HTTPS/TLS]
    HTTPS --> CORS[CORS 정책]
    CORS --> Auth[인증 미들웨어]
    Auth --> RBAC[RBAC 검사]
    RBAC --> Validation[입력 검증]
    Validation --> SQL[SQL Injection 방지]
    SQL --> RateLimit[Rate Limiting]
    RateLimit --> API[API 엔드포인트]
```

---

## 성능 아키텍처

### 캐싱 전략

```mermaid
graph LR
    Request[API 요청] --> Cache{캐시 확인}
    Cache -->|히트| Return[캐시 반환<br/>TTL: 5min/1min]
    Cache -->|미스| DB[DB 조회]
    DB --> Store[캐시 저장]
    Store --> Return
    Return --> Response[응답]

    Write[데이터 쓰기] --> Invalidate[캐시 무효화]
    Invalidate --> Update[DB 업데이트]
```

### 성능 최적화 포인트

1. **서버 캐싱**
   - Locations/Shipments/Legs: 5분 TTL
   - Events: 1분 TTL
   - 캐시 히트율: 약 50% (예상)

2. **클라이언트 최적화**
   - React 메모이제이션
   - 코드 스플리팅
   - 이미지 최적화

3. **데이터베이스**
   - 인덱스 활용
   - 쿼리 최적화
   - 배치 처리

---

## 확장성 고려사항

### 수평 확장

```mermaid
graph TB
    LB[로드 밸런서] --> API1[API 인스턴스 1]
    LB --> API2[API 인스턴스 2]
    LB --> API3[API 인스턴스 N]

    API1 --> SharedDB[(공유 DB)]
    API2 --> SharedDB
    API3 --> SharedDB

    API1 --> SharedCache[(Redis Cache)]
    API2 --> SharedCache
    API3 --> SharedCache
```

### 데이터베이스 마이그레이션 경로

```mermaid
graph LR
    Current[DuckDB<br/>현재] --> Option1[PostgreSQL<br/>프로덕션]
    Current --> Option2[DuckDB Cluster<br/>확장]
    Option1 --> Scale[수평 확장]
    Option2 --> Scale
```

---

## 모니터링 및 로깅

### 로깅 계층

```mermaid
graph TD
    App[애플리케이션] --> Logger[로거]
    Logger --> Console[콘솔 출력]
    Logger --> File[파일 로그]
    Logger --> Remote[원격 로깅<br/>계획]

    Metrics[메트릭] --> CacheHit[캐시 히트율]
    Metrics --> ResponseTime[응답 시간]
    Metrics --> ErrorRate[에러율]
```

---

## API 엔드포인트 구조

### REST API

```mermaid
graph TB
    API[FastAPI App] --> Auth[인증 엔드포인트]
    API --> Data[데이터 엔드포인트]
    API --> WS[WebSocket]

    Auth --> Login[POST /api/auth/login]
    Auth --> Me[GET /api/auth/me]

    Data --> Locations[GET /api/locations]
    Data --> Shipments[GET /api/shipments]
    Data --> Legs[GET /api/legs]
    Data --> Events[GET /api/events]
    Data --> DemoEvent[POST /api/events/demo]

    WS --> WSEndpoint[WS /ws/events]
```

---

## 데이터 저장 전략

### 계층화된 저장소

```mermaid
graph TB
    App[애플리케이션] --> Cache[메모리 캐시<br/>TTLCache]
    Cache -->|Cache Miss| DB[DuckDB<br/>Primary]
    DB -->|Fallback| CSV[CSV Files<br/>Backup]

    Write[데이터 쓰기] --> DB
    Write --> CSV
    Write --> Invalidate[캐시 무효화]
```

---

## 변경 이력

- **2026-01-08**: 초기 아키텍처 문서 작성
- **2026-01-08**: Phase 3.1, 3.2 반영

---

**문서 버전**: 1.1
**최종 업데이트**: 2026-01-08
