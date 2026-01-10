# MOSB Logistics Dashboard

**실시간 물류 추적 및 운영 관리를 위한 웹 기반 대시보드**

[![Next.js](https://img.shields.io/badge/Next.js-16.1.1-black)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-18.2.0-blue)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.119.0-green)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9.3-blue)](https://www.typescriptlang.org/)

## 📋 목차

- [개요](#개요)
- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [시작하기](#시작하기)
- [문서](#문서)
- [개발 진행 상황](#개발-진행-상황)

## 🎯 개요

MOSB Logistics Dashboard는 실시간 물류 추적 및 운영 관리를 위한 웹 기반 대시보드입니다. Streamlit보다 더 세련된 UI와 확장 가능한 아키텍처를 제공합니다.

### 핵심 특징

- 🗺️ **실시간 지도 시각화**: Deck.gl + MapLibre 기반 고성능 지도 렌더링
- 🔐 **역할 기반 접근 제어**: JWT + RBAC 기반 보안 시스템
- ⚡ **실시간 이벤트 스트리밍**: WebSocket 기반 실시간 업데이트
- 📊 **KPI 대시보드**: 실시간 물류 지표 모니터링
- 🚀 **고성능 캐싱**: 서버/클라이언트 캐싱으로 빠른 응답 시간

## ✨ 주요 기능

### 현재 구현된 기능 (MVP)

- ✅ 실시간 지도 시각화 (Locations, Shipments, Legs)
- ✅ 이벤트 타임라인 및 필터링
- ✅ KPI 대시보드 (Planned, In Transit, Arrived, Delayed)
- ✅ JWT 기반 인증 시스템
- ✅ 역할 기반 접근 제어 (OPS, FINANCE, COMPLIANCE, ADMIN)
- ✅ WebSocket 실시간 이벤트 스트리밍
- ✅ DuckDB 기반 데이터 저장 (CSV fallback 지원)
- ✅ 서버 캐싱 (TTLCache)
- ✅ **Client-Only Dashboard** (Phase 4.1, 2026-01-10)
  - 클라이언트 사이드 지오펜스 필터링 및 판정
  - 히트맵 집계 및 시각화
  - ETA 웨지 계산 및 3D 시각화
  - 배치 WebSocket 처리 (500ms)
  - Zustand 기반 상태 관리
  - MapLibre + DeckGL 동기화

### 계획된 기능

- 🔄 Port/Berth 상세 정보
- ✅ ~~Geofence 진입/이탈 알림~~ (Client-Only Dashboard에 구현됨)
- ✅ ~~Heatmap 시각화~~ (Client-Only Dashboard에 구현됨)
- ✅ ~~ETA 예측 콘~~ (Client-Only Dashboard에 구현됨)
- 🔄 감사 로그
- 🔄 CI/CD 파이프라인

## 🛠️ 기술 스택

### Frontend

| 기술 | 버전 | 용도 |
|------|------|------|
| Next.js | 16.1.1 | React 프레임워크 |
| React | 18.2.0 | UI 라이브러리 |
| Deck.gl | 9.0.0 | 지도 레이어 렌더링 |
| MapLibre | 4.0.0 | 지도 타일 제공 |
| TypeScript | 5.9.3 | 타입 안전성 |
| Zustand | 4.5.2 | 상태 관리 |
| Turf.js | 7.0.0 | 지리공간 분석 |
| `@deck.gl/aggregation-layers` | 9.0.0 | 히트맵 레이어 |
| `@deck.gl/extensions` | 9.0.0 | 마스크 확장 |
| `@turf/boolean-point-in-polygon` | 7.0.0 | 지오펜스 판정 |
| `cross-env` | 7.0.3 | 환경 변수 관리 |

### Backend

| 기술 | 버전 | 용도 |
|------|------|------|
| FastAPI | 0.119.0 | REST API 서버 |
| Uvicorn | 0.30.0 | ASGI 서버 |
| DuckDB | 1.3.2 | 데이터 저장 |
| Pydantic | 2.0.0 | 데이터 검증 |
| python-jose | 3.3.0 | JWT 처리 |
| cachetools | 5.5.0 | 메모리 캐싱 |

## 📁 프로젝트 구조

```
MOSB_Logistics_LiveMap_MVP_v2/
├── docs/                          # 프로젝트 문서
│   ├── AGENTS.md                  # 아키텍처 가이드
│   ├── System_Architecture.md     # 시스템 아키텍처 문서
│   ├── Implementation_Progress.md # 구현 진행 상황
│   ├── Runtime_Verification_Results.md # 런타임 검증 결과
│   ├── MOSB Logistics Dashboard.MD
│   ├── constitution.md            # 프로젝트 규칙
│   │
│   ├── guides/                    # 가이드 문서
│   │   ├── Client-Only_Dashboard_Guide.md
│   │   ├── Server_Restart_Guide.md
│   │   ├── JSX_Error_Resolution_Summary.md
│   │   └── JSX_Runtime_Error_Troubleshooting.md
│   │
│   ├── plans/                     # 계획 문서
│   │   ├── Client-Only_Implementation_Plan.md
│   │   └── Phase_4.1_Hybrid_Integration_Checklist.py
│   │
│   ├── work-logs/                 # 작업 로그
│   │   ├── work-log-2026-01-09.md
│   │   └── work-log-2026-01-10.md
│   │
│   ├── dev-tools/                 # 개발 도구 문서
│   │   └── cursor/
│   │       ├── Cursor_Project_AutoSetup_Guide.md
│   │       ├── Cursor_Project_Setup_v1.3.md
│   │       └── Cursor_Config_Patch_v1_Guide.md
│   │
│   ├── en/                        # 영어 문서
│   │   ├── server-ops.md
│   │   ├── release-notes.md
│   │   └── CHANGELOG.md
│   │
│   └── kr/                        # 한국어 문서
│       ├── server-ops.md
│       ├── release-notes.md
│       └── CHANGELOG.md
├── mosb_logistics_dashboard_next_fastapi_mvp/
│   ├── frontend/                  # Next.js Frontend
│   │   ├── pages/                 # 페이지 컴포넌트
│   │   │   ├── index.tsx          # 메인 대시보드
│   │   │   └── dashboard-client-only.tsx # Client-Only Dashboard
│   │   ├── components/            # UI 컴포넌트
│   │   │   ├── Login.tsx          # 로그인 컴포넌트
│   │   │   └── client-only/       # Client-Only Dashboard 컴포넌트
│   │   │       ├── ClientOnlyDashboard.tsx
│   │   │       └── ClientOnlyMap.tsx
│   │   ├── lib/                   # API 클라이언트, 인증
│   │   │   ├── api.ts             # REST API 클라이언트
│   │   │   ├── auth.ts            # 인증 서비스
│   │   │   └── client-only/       # Client-Only 유틸리티
│   │   │       ├── geofence.ts    # 지오펜스 판정
│   │   │       ├── heatmap.ts     # 히트맵 집계
│   │   │       ├── eta.ts         # ETA 웨지 계산
│   │   │       └── ws.ts          # WebSocket 배치 처리
│   │   ├── hooks/                 # React Hooks
│   │   │   ├── useWebSocket.ts    # WebSocket Hook
│   │   │   ├── useBatchedClientOnlyWs.ts # 배치 WebSocket
│   │   │   └── useClientOnlyGeofences.ts # 지오펜스 Hook
│   │   ├── store/                 # Zustand 스토어
│   │   │   └── useClientOnlyStore.ts
│   │   ├── types/                 # TypeScript 타입 정의
│   │   │   ├── logistics.ts       # 물류 타입
│   │   │   └── clientOnly.ts      # Client-Only 타입
│   │   ├── public/data/           # 정적 데이터
│   │   │   └── geofence.json      # GeoJSON 지오펜스 데이터
│   │   └── styles/                # 스타일
│   │       └── globals.css
│   └── backend/                   # FastAPI Backend
│       ├── main.py                # FastAPI 앱
│       ├── auth.py                # JWT 인증
│       ├── rbac.py                # 역할 기반 접근 제어
│       ├── db.py                  # DuckDB 통합
│       ├── cache.py               # 캐싱 레이어
│       ├── models.py              # Pydantic 모델
│       ├── tests/                 # 테스트 코드
│       │   ├── test_main.py
│       │   ├── test_db.py
│       │   ├── test_cache.py
│       │   └── test_auth.py
│       └── data/                  # CSV 데이터 파일
│           ├── locations.csv
│           ├── shipments.csv
│           ├── legs.csv
│           └── events.csv
├── start-servers.ps1              # 서버 자동화 스크립트 (Windows)
└── README.md                      # 이 파일
```

## 🚀 시작하기

### 사전 요구사항

- **Node.js**: 18.x 이상
- **Python**: 3.11 이상
- **npm** 또는 **yarn**
- **PowerShell 7.x** (Windows, 서버 자동화 스크립트 사용 시)

### 설치 및 실행

#### 방법 1: 자동화 스크립트 사용 (권장)

Windows에서 PowerShell 스크립트를 사용하여 서버를 자동으로 시작할 수 있습니다:

```powershell
# 프로젝트 루트 디렉토리에서 실행
.\start-servers.ps1 -CleanCache

# Frontend만 시작 (캐시 정리 포함)
.\start-servers.ps1 -FrontendOnly -CleanCache

# Backend만 시작
.\start-servers.ps1 -BackendOnly

# 서버 확인 건너뛰고 시작
.\start-servers.ps1 -SkipCheck
```

**스크립트 기능**:
- ✅ 자동 포트 충돌 감지 및 해결
- ✅ 자동 `.next` 캐시 정리 (`-CleanCache` 옵션)
- ✅ 자동 `next-env.d.ts` 수정 (잘못된 import 제거)
- ✅ 글로벌 `NODE_ENV=production` 자동 감지 및 제거
- ✅ `cross-env` 자동 설치 확인 및 설치
- ✅ 환경 변수 자동 설정
- ✅ 백엔드 Job ID 추적 (쉬운 종료)
- ✅ 프론트엔드 서버를 새 PowerShell 창에서 실행 (로그 확인 가능)

자세한 내용은 [docs/kr/server-ops.md](docs/kr/server-ops.md) 또는 [docs/en/server-ops.md](docs/en/server-ops.md)를 참조하세요.

#### 방법 2: 수동 실행

##### 1. 저장소 클론

```bash
git clone https://github.com/macho715/MOSB_LOGISTICS.git
cd MOSB_Logistics_LiveMap_MVP_v2
```

##### 2. Backend 설정

```bash
cd mosb_logistics_dashboard_next_fastapi_mvp/backend

# 가상환경 생성 (선택사항)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 필요한 값 수정

# 서버 실행
uvicorn main:app --reload --port 8000
```

Backend는 `http://localhost:8000`에서 실행됩니다.

##### 3. Frontend 설정

```bash
cd mosb_logistics_dashboard_next_fastapi_mvp/frontend

# 의존성 설치
npm install

# 환경 변수 설정
cp .env.local.example .env.local
# .env.local 파일을 열어 API_BASE URL 확인

# 개발 서버 실행
npm run dev
```

Frontend는 `http://localhost:3000`에서 실행됩니다.

### 데모 사용자

로그인 테스트용 데모 사용자:

| 사용자명 | 비밀번호 | 역할 |
|---------|---------|------|
| `ops_user` | `ops123` | OPS |
| `finance_user` | `finance123` | FINANCE |
| `compliance_user` | `compliance123` | COMPLIANCE |
| `admin` | `admin123` | ADMIN |

### 테스트 실행

```bash
# Backend 테스트
cd mosb_logistics_dashboard_next_fastapi_mvp/backend
pytest -q -v

# Frontend 타입 체크
cd mosb_logistics_dashboard_next_fastapi_mvp/frontend
npm run type-check

# Frontend 린트
npm run lint
```

## 📚 문서

프로젝트의 상세 문서는 `docs/` 디렉토리에서 확인할 수 있습니다:

### 핵심 문서
- **[AGENTS.md](docs/AGENTS.md)**: 프로젝트 아키텍처 가이드 및 개발 가이드
- **[System_Architecture.md](docs/System_Architecture.md)**: 시스템 아키텍처 문서 (Mermaid 다이어그램 포함)
- **[Implementation_Progress.md](docs/Implementation_Progress.md)**: 구현 진행 상황 및 검증 결과
- **[MOSB Logistics Dashboard.MD](docs/MOSB%20Logistics%20Dashboard.MD)**: 상세 구현 가이드

### 가이드 문서
- **[Client-Only_Dashboard_Guide.md](docs/guides/Client-Only_Dashboard_Guide.md)**: Client-Only Dashboard 사용 가이드
- **[Runtime_Verification_Results.md](docs/Runtime_Verification_Results.md)**: 런타임 검증 결과 및 Step 4 체크리스트
- **[Server_Restart_Guide.md](docs/guides/Server_Restart_Guide.md)**: 서버 재시작 가이드
- **[JSX_Error_Resolution_Summary.md](docs/guides/JSX_Error_Resolution_Summary.md)**: JSX 런타임 오류 해결 요약
- **[JSX_Runtime_Error_Troubleshooting.md](docs/guides/JSX_Runtime_Error_Troubleshooting.md)**: JSX 런타임 오류 상세 해결 가이드

### 계획 문서
- **[Client-Only_Implementation_Plan.md](docs/plans/Client-Only_Implementation_Plan.md)**: Client-Only Dashboard 구현 계획
- **[Phase_4.1_Hybrid_Integration_Checklist.py](docs/plans/Phase_4.1_Hybrid_Integration_Checklist.py)**: Phase 4.1 통합 체크리스트 (Python 스크립트)

### 작업 로그
- **[work-log-2026-01-09.md](docs/work-logs/work-log-2026-01-09.md)**: 2026-01-09 작업 로그
- **[work-log-2026-01-10.md](docs/work-logs/work-log-2026-01-10.md)**: 2026-01-10 작업 로그

### 개발 도구
- **[Cursor 설정 가이드](docs/dev-tools/cursor/)**: Cursor IDE 설정 및 자동화 가이드
  - [Cursor_Project_AutoSetup_Guide.md](docs/dev-tools/cursor/Cursor_Project_AutoSetup_Guide.md)
  - [Cursor_Project_Setup_v1.3.md](docs/dev-tools/cursor/Cursor_Project_Setup_v1.3.md)
  - [Cursor_Config_Patch_v1_Guide.md](docs/dev-tools/cursor/Cursor_Config_Patch_v1_Guide.md)

### 운영 문서
- **[docs/en/server-ops.md](docs/en/server-ops.md)**: 서버 운영 가이드 (English)
- **[docs/kr/server-ops.md](docs/kr/server-ops.md)**: 서버 운영 가이드 (한국어)
- **[docs/en/release-notes.md](docs/en/release-notes.md)**: 릴리스 노트 (English)
- **[docs/kr/release-notes.md](docs/kr/release-notes.md)**: 릴리스 노트 (한국어)

## 📊 개발 진행 상황

### ✅ 완료된 Phase

- **Phase 1**: Frontend 타입 정의, API 클라이언트, WebSocket Hook
- **Phase 2**: Backend Pydantic 모델, 테스트 코드, 환경 변수 템플릿
- **Phase 3.1**: DuckDB 통합, 캐싱 레이어
- **Phase 3.2**: JWT 인증, RBAC, Frontend 인증 통합
- **Phase 4.1**: Client-Only Dashboard (2026-01-10)
  - 클라이언트 사이드 지오펜스 필터링 및 판정
  - 히트맵 집계 및 시각화
  - ETA 웨지 계산 및 3D 시각화
  - 배치 WebSocket 처리 (500ms)
  - Zustand 기반 상태 관리
  - MapLibre + DeckGL 동기화
  - `start-servers.ps1` 스크립트 개선

### 🔄 진행 중 / 계획

- **Phase 3.3**: 성능 최적화 (서버 캐시, 클라이언트 메모이제이션)
- **Phase 3.4**: CI/CD 파이프라인
- **Phase 4.2**: 런타임 검증 완료 (Step 4 진행 중)
- **Phase 5**: 프로덕션 배포 준비

자세한 내용은 [Implementation_Progress.md](docs/Implementation_Progress.md) 및 [Runtime_Verification_Results.md](docs/Runtime_Verification_Results.md)를 참조하세요.

## 🔒 보안

- JWT 기반 인증 시스템
- 역할 기반 접근 제어 (RBAC)
- 환경 변수로 민감 정보 관리
- CORS 정책 설정

**중요**: 프로덕션 환경에서는 반드시 `.env` 파일의 `JWT_SECRET_KEY`를 변경하세요.

## 🤝 기여

이 프로젝트는 내부 프로젝트입니다. 기여를 원하시면 프로젝트 관리자에게 문의하세요.

## 📝 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.

## 📞 문의

프로젝트 관련 문의사항이 있으시면 이슈를 생성해주세요.

---

**버전**: MVP v2
**최종 업데이트**: 2026-01-10
