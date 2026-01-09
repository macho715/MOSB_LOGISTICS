# MOSB Logistics Dashboard

**실시간 물류 추적 및 운영 관리를 위한 웹 기반 대시보드**

[![Next.js](https://img.shields.io/badge/Next.js-14.2.0-black)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-18.2.0-blue)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.119.0-green)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0.0-blue)](https://www.typescriptlang.org/)

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

### 계획된 기능

- 🔄 Port/Berth 상세 정보
- 🔄 Geofence 진입/이탈 알림
- 🔄 Heatmap 시각화
- 🔄 ETA 예측 콘
- 🔄 감사 로그
- 🔄 CI/CD 파이프라인

## 🛠️ 기술 스택

### Frontend

| 기술 | 버전 | 용도 |
|------|------|------|
| Next.js | 14.2.0 | React 프레임워크 |
| React | 18.2.0 | UI 라이브러리 |
| Deck.gl | 9.0.0 | 지도 레이어 렌더링 |
| MapLibre | 4.0.0 | 지도 타일 제공 |
| TypeScript | 5.0.0 | 타입 안전성 |

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
│   └── MOSB Logistics Dashboard.MD
├── mosb_logistics_dashboard_next_fastapi_mvp/
│   ├── frontend/                  # Next.js Frontend
│   │   ├── pages/                 # 페이지 컴포넌트
│   │   ├── components/            # UI 컴포넌트
│   │   ├── lib/                   # API 클라이언트, 인증
│   │   ├── hooks/                 # React Hooks
│   │   └── types/                 # TypeScript 타입 정의
│   └── backend/                   # FastAPI Backend
│       ├── main.py                # FastAPI 앱
│       ├── auth.py                # JWT 인증
│       ├── rbac.py                # 역할 기반 접근 제어
│       ├── db.py                  # DuckDB 통합
│       ├── cache.py               # 캐싱 레이어
│       ├── models.py              # Pydantic 모델
│       ├── tests/                 # 테스트 코드
│       └── data/                  # CSV 데이터 파일
└── README.md                      # 이 파일
```

## 🚀 시작하기

### 사전 요구사항

- **Node.js**: 18.x 이상
- **Python**: 3.11 이상
- **npm** 또는 **yarn**

### 설치 및 실행

#### 1. 저장소 클론

```bash
git clone https://github.com/macho715/MOSB_LOGISTICS.git
cd MOSB_Logistics_LiveMap_MVP_v2
```

#### 2. Backend 설정

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

#### 3. Frontend 설정

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

- **[AGENTS.md](docs/AGENTS.md)**: 프로젝트 아키텍처 가이드 및 개발 가이드
- **[System_Architecture.md](docs/System_Architecture.md)**: 시스템 아키텍처 문서 (Mermaid 다이어그램 포함)
- **[Implementation_Progress.md](docs/Implementation_Progress.md)**: 구현 진행 상황 및 검증 결과
- **[MOSB Logistics Dashboard.MD](docs/MOSB%20Logistics%20Dashboard.MD)**: 상세 구현 가이드

## 📊 개발 진행 상황

### ✅ 완료된 Phase

- **Phase 1**: Frontend 타입 정의, API 클라이언트, WebSocket Hook
- **Phase 2**: Backend Pydantic 모델, 테스트 코드, 환경 변수 템플릿
- **Phase 3.1**: DuckDB 통합, 캐싱 레이어
- **Phase 3.2**: JWT 인증, RBAC, Frontend 인증 통합

### 🔄 진행 중 / 계획

- **Phase 3.3**: 성능 최적화 (서버 캐시, 클라이언트 메모이제이션)
- **Phase 3.4**: CI/CD 파이프라인
- **Phase 4**: 확장 기능 (Geofence, Heatmap, ETA 예측)

자세한 내용은 [Implementation_Progress.md](docs/Implementation_Progress.md)를 참조하세요.

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
**최종 업데이트**: 2026-01-08
