# Client-Only Dashboard 런타임 검증 결과

**검증 일시**: 2026-01-10
**검증 환경**: Windows, PowerShell

---

## 검증 항목 및 결과

### 1. 사전 준비 사항 확인 ✅

#### 1.1 환경 변수 설정
- **상태**: `.env.local` 파일은 `.gitignore`에 포함되어 수동 생성 필요
- **권장 사항**: `mosb_logistics_dashboard_next_fastapi_mvp/frontend/.env.local` 파일 생성
  ```
  NEXT_PUBLIC_API_BASE=http://localhost:8000
  NEXT_PUBLIC_WS_RECONNECT_DELAY=3000
  NEXT_PUBLIC_WS_MAX_RECONNECT_ATTEMPTS=10
  ```
- **참고**: 환경 변수가 없어도 기본값(`http://localhost:8000`)으로 동작

#### 1.2 의존성 설치 확인 ✅
- **Backend 의존성**: ✅ 모든 필수 패키지 설치 확인 (fastapi, uvicorn, duckdb, cachetools)
- **Frontend 의존성**: ✅ zustand 설치 확인 (`zustand@4.5.7`)
  - 기타 의존성: package.json에 정의됨, npm install 완료

#### 1.3 데이터 파일 확인 ✅
- **CSV 데이터**: ✅ 모든 파일 존재 확인
  - `locations.csv`
  - `shipments.csv`
  - `legs.csv`
  - `events.csv`
- **GeoJSON 데이터**: ✅ `public/data/geofence.json` 존재 확인

---

### 2. 백엔드 서버 실행 및 검증 ✅

#### 2.1 서버 시작 ✅
- **상태**: ✅ 백엔드 서버 정상 실행
- **포트**: 8000
- **프로세스 ID**: 39848

#### 2.2 API 엔드포인트 검증 ✅
- **인증 엔드포인트**:
  - ✅ `POST /api/auth/login` - 로그인 성공, 토큰 발급 확인
- **데이터 엔드포인트** (토큰 필요):
  - ✅ `GET /api/locations` → 8개 locations 반환
  - ✅ `GET /api/legs` → 6개 legs 반환
  - ✅ `GET /api/events` → 28개 events 반환
- **Demo 이벤트 생성**:
  - ✅ `POST /api/events/demo` - 이벤트 생성 성공 (Event ID: EV-e3e15e2e)

#### 2.3 WebSocket 엔드포인트
- **엔드포인트**: `ws://localhost:8000/ws/events`
- **상태**: ✅ 백엔드 코드에서 엔드포인트 정의 확인 (`/ws/events`)
- **참고**: 실제 WebSocket 연결 테스트는 브라우저에서 필요

---

### 3. 프론트엔드 서버 실행 및 검증 ⚠️

#### 3.1 서버 시작 ✅
- **상태**: ✅ 프론트엔드 서버 정상 실행
- **포트**: 3000
- **프로세스 ID**: 34204

#### 3.2 서버 응답 확인 ⚠️
- **URL**: `http://localhost:3000`
- **상태**: 서버 실행 중이나 초기 컴파일 중일 수 있음
- **참고**: Next.js 개발 서버는 첫 빌드 시 시간이 소요됨 (30-60초)
- **다음 단계**: 브라우저에서 직접 접근하여 확인 필요

---

### 4. 브라우저 기반 기능 테스트 (수동 테스트 필요)

다음 항목들은 브라우저에서 직접 확인이 필요합니다:

#### 4.1 페이지 접근
- **URL**: `http://localhost:3000/dashboard-client-only`
- **확인 필요**: 로그인 화면 또는 인증 진행 중 화면 표시

#### 4.2 인증 테스트
- **로그인 화면 확인**:
  - [ ] 로그인 폼 표시
  - [ ] 데모 사용자 안내 메시지 표시
- **로그인 성공**:
  - [ ] `ops_user / ops123` 로그인 시도
  - [ ] 로그인 성공 후 대시보드 화면 표시
  - [ ] 상단 헤더에 사용자 정보 표시 ("User: ops_user (OPS)")
  - [ ] Logout 버튼 표시

#### 4.3 초기 데이터 로딩 테스트
브라우저 개발자 도구 (F12) → Network 탭 확인:
- [ ] `GET /api/locations` → 200 OK, 8개 locations
- [ ] `GET /api/legs` → 200 OK, 6개 legs
- [ ] `GET /api/events` → 200 OK, 28개 이상 events
- [ ] `GET /data/geofence.json` → 200 OK, JSON 파싱 성공
- [ ] JavaScript 오류 없음 (콘솔 확인)

#### 4.4 지도 렌더링 테스트
- [ ] 지도가 화면에 표시됨
- [ ] 다크 테마 스타일 적용 (Carto Dark Matter)
- [ ] 아부다비 근처 지역 표시
- [ ] 지오펜스 아웃라인 표시 (8개 폴리곤)
- [ ] 이벤트 포인트 표시
- [ ] Legs 아크 표시 (6개)
- [ ] 위치 라벨 표시

#### 4.5 KPI 패널 테스트
- [ ] "Shipments: X" (X > 0)
- [ ] "Planned: X" 표시
- [ ] "In-Transit: X" 표시
- [ ] "Arrived: X" 표시
- [ ] "Delayed: X" 표시
- [ ] "Hold: X" 표시
- [ ] "Unknown: X" 표시
- [ ] "Events in window: X" (X ≥ 28)

#### 4.6 WebSocket 연결 테스트
브라우저 개발자 도구 (F12) → Network 탭 → WS 필터:
- [ ] `ws://localhost:8000/ws/events` 연결 성공
- [ ] `hello` 메시지 수신 (연결 시)
- [ ] `ping` 메시지 주기적 수신 (10초마다)
- [ ] 별도 터미널에서 `POST /api/events/demo` 실행
- [ ] 대시보드에서 새 이벤트 포인트 즉시 표시
- [ ] "Events in window" 카운트 증가

#### 4.7 레이어 토글 테스트
- [ ] Geofence mask 체크/해제
- [ ] Heatmap 체크/해제
- [ ] ETA wedge 체크/해제

#### 4.8 시간 윈도우 조절 테스트
- [ ] 12시간으로 변경 → 오래된 이벤트 제거
- [ ] 48시간으로 변경 → 더 많은 이벤트 표시
- [ ] "Events in window" 카운트 업데이트

#### 4.9 히트맵 필터 테스트
- [ ] "enter" 선택 → enter 이벤트만 히트맵에 표시
- [ ] "exit" 선택 → exit 이벤트만 히트맵에 표시

#### 4.10 지도 인터랙션 테스트
- [ ] 마우스 휠로 확대/축소 동작
- [ ] 마우스 드래그로 지도 이동
- [ ] DeckGL 레이어가 MapLibre와 동기화

#### 4.11 지오펜스 판정 테스트
- [ ] 초록색 포인트: `enter` 이벤트
- [ ] 빨간색 포인트: `exit` 이벤트
- [ ] 파란색 포인트: `move` 이벤트

#### 4.12 성능 테스트
브라우저 개발자 도구 (F12) → Performance 탭:
- [ ] 초기 로딩 시간 < 5초
- [ ] 이벤트 업데이트 시 프레임 드롭 없음 (60 FPS 유지)
- [ ] 메모리 사용량 안정적 (< 500MB 권장)
- [ ] 10분간 대시보드 유지 후 메모리 누수 확인

---

### 5. 오류 시나리오 테스트 (수동 테스트 필요)

#### 5.1 백엔드 서버 다운
- [ ] 백엔드 서버 종료
- [ ] WebSocket 연결 종료 감지
- [ ] 자동 재연결 시도 (백오프: 500ms → 1s → 2s → ... → 10s)
- [ ] 재연결 성공 시 정상 동작 재개

#### 5.2 네트워크 오류
- [ ] 네트워크 연결 끊김
- [ ] WebSocket 연결 종료 감지
- [ ] 재연결 시도 (최대 10초 백오프)
- [ ] 네트워크 복구 시 자동 재연결

#### 5.3 인증 토큰 만료
- [ ] 토큰 만료 후 API 호출
- [ ] 401 Unauthorized 응답
- [ ] 자동 로그아웃
- [ ] 로그인 화면으로 리다이렉트

---

## 검증 체크리스트 요약

### 완료된 항목 ✅
- [x] TypeScript 컴파일 성공
- [x] Next.js 빌드 성공
- [x] 백엔드 서버 실행 성공
- [x] 프론트엔드 서버 실행 성공
- [x] 백엔드 API 엔드포인트 검증 완료
  - [x] 로그인 엔드포인트
  - [x] Locations 엔드포인트 (8개)
  - [x] Legs 엔드포인트 (6개)
  - [x] Events 엔드포인트 (28개)
  - [x] Demo 이벤트 생성
- [x] **JSX 런타임 오류 해결 완료** ✅
  - [x] 글로벌 `NODE_ENV=production` 제거 (자동화됨)
  - [x] `package.json`에 `cross-env NODE_ENV=development` 추가
  - [x] `next-env.d.ts`에서 잘못된 import 제거 (자동화됨)
  - [x] `tsconfig.json` `jsx: "react-jsx"` 설정 확인
  - [x] `.next` 캐시 정리 (자동화됨)
  - [x] 브라우저 콘솔에서 JSX 오류 해결 확인 (루트 페이지 `/` 정상 작동)
- [x] **`start-servers.ps1` 스크립트 개선 완료** ✅
  - [x] 자동 `next-env.d.ts` 수정 기능
  - [x] 자동 `.next` 캐시 정리 기능 (`-CleanCache` 옵션)
  - [x] 프론트엔드 서버를 새 PowerShell 창에서 실행
  - [x] 글로벌 `NODE_ENV=production` 자동 감지 및 제거
  - [x] `cross-env` 자동 설치 확인 및 설치
  - [x] 백엔드 Job 스코프 환경 변수 전달 개선
  - [x] PowerShell Jobs 정리 기능 강화
  - [x] 백엔드 Job ID 추적
- [x] 검증 결과 문서화 완료

### 수동 테스트 필요 항목 ⚠️ (서버 재시작 후)

**⚠️ 중요**: 프론트엔드 서버 재시작 후 다음 항목들을 테스트해야 합니다.
- 참고: `docs/Server_Restart_Guide.md` 참조

**기능 테스트**:
- [ ] 로그인 화면 표시
- [ ] 로그인 성공
- [ ] 초기 데이터 로딩 (Locations, Legs, Events)
- [ ] 지도 렌더링 (MapLibre + DeckGL)
- [ ] WebSocket 연결 성공
- [ ] 이벤트 포인트 표시
- [ ] KPI 패널 업데이트
- [ ] 레이어 토글 동작
- [ ] 시간 윈도우 조절
- [ ] 히트맵 필터
- [ ] 실시간 이벤트 업데이트
- [ ] 지오펜스 판정 (enter/exit 색상)

**고급 테스트**:
- [ ] 성능 테스트 통과
- [ ] 오류 처리 검증

---

## 발견된 이슈

### 이슈 1: .env.local 파일 자동 생성 불가
- **원인**: `.env.local` 파일이 `.gitignore`에 포함되어 있어 자동 생성 불가
- **해결책**: 수동으로 `mosb_logistics_dashboard_next_fastapi_mvp/frontend/.env.local` 파일 생성
- **영향**: 낮음 (기본값으로 동작)

### 이슈 2: 프론트엔드 서버 JSX 런타임 오류 ✅ **해결 완료**
- **증상**: 브라우저 콘솔에 `jsxDEV is not a function` 오류 발생
- **원인**:
  - ✅ **글로벌 NODE_ENV=production 설정** (가장 큰 원인)
  - ✅ `next-env.d.ts`에 잘못된 import (`import "./.next/dev/types/routes.d.ts"`)
  - ✅ `tsconfig.json` 설정: `jsx: "react-jsx"` (올바른 설정)
- **해결**:
  - ✅ 글로벌 `NODE_ENV` 제거: `$env:NODE_ENV = $null`
  - ✅ `package.json` dev 스크립트에 `cross-env NODE_ENV=development` 추가
  - ✅ `next-env.d.ts`에서 잘못된 import 제거
  - ✅ `tsconfig.json` `jsx: "react-jsx"` 설정 (올바름)
  - ✅ `.next` 캐시 정리
- **상태**: ✅ **해결 완료** (JSX 런타임 오류 없음 확인)
- **검증**: 브라우저 콘솔에서 `jsxDEV is not a function` 오류 사라짐
- **결과**: 루트 페이지(`/`) 정상 작동, JSX 런타임 오류 없음

### 이슈 3: `/dashboard-client-only` 라우트 404 오류 ⚠️
- **증상**: `/dashboard-client-only` 접근 시 "404: This page could not be found" 오류
- **원인**:
  - 파일은 존재함: `pages/dashboard-client-only.tsx` ✅
  - 서버가 아직 해당 라우트를 컴파일하지 않았을 수 있음
  - Next.js 개발 서버의 첫 빌드 시간 문제 가능
- **해결책**:
  1. 서버 재시작 후 30-60초 대기 (라우트 컴파일 시간)
  2. 페이지 파일이 올바른 위치에 있는지 확인: `pages/dashboard-client-only.tsx`
  3. 파일 이름과 경로 대소문자 확인 (Next.js는 대소문자 구분)
- **상태**: 파일 존재 확인, 컴파일 대기 중
- **영향**: 중간 (특정 라우트만 접근 불가)

### 이슈 4: 프론트엔드 서버 초기 컴파일 시간
- **원인**: Next.js 개발 서버 첫 빌드 시 컴파일 시간 소요
- **해결책**: 서버 시작 후 30-60초 대기 후 브라우저 접근
- **영향**: 낮음 (일회성, 개발 환경에서만 발생)

---

## Step 4: 런타임 검증 절차 (2026-01-10 업데이트)

### 4.1 개선된 `start-servers.ps1` 스크립트 활용 ✅

**✅ 주요 개선 사항**:
1. **자동 `next-env.d.ts` 수정**
   - 잘못된 import (`import "./.next/dev/types/routes.d.ts"`) 자동 감지 및 제거
   - Windows/Unix 줄바꿈 모두 지원
   - 연속된 빈 줄 정리

2. **자동 `.next` 캐시 정리** (`-CleanCache` 옵션)
   - Next.js 빌드 캐시 자동 삭제
   - JSX 런타임 오류 방지

3. **프론트엔드 서버를 새 PowerShell 창에서 실행**
   - 서버 로그 확인 가능
   - `cross-env` 정상 실행 보장
   - 디버깅 용이

4. **글로벌 `NODE_ENV=production` 자동 감지 및 제거**
   - JSX 런타임 오류 근본 원인 해결
   - 개발 모드 강제 실행

5. **`cross-env` 자동 설치 확인 및 설치**
   - `package.json`과 `node_modules` 모두 확인
   - 누락 시 자동 설치

6. **백엔드 Job 스코프 환경 변수 전달 개선**
   - `.env` 파일 파싱을 Job 내부에서 수행
   - 환경 변수 정확히 전달

7. **PowerShell Jobs 정리 기능 강화**
   - 관련 Jobs 자동 종료
   - 포트 해제 대기 로직 (최대 5초)
   - 고아 프로세스 방지

8. **백엔드 Job ID 추적**
   - 스크립트 스코프 변수에 저장
   - 쉬운 종료 명령 제공

**권장 사용법**:

```powershell
# Frontend만 시작 (캐시 정리 포함) - 가장 권장
.\start-servers.ps1 -FrontendOnly -CleanCache

# Backend + Frontend 동시 시작 (캐시 정리 포함)
.\start-servers.ps1 -CleanCache

# Backend만 시작
.\start-servers.ps1 -BackendOnly

# 서버 확인 건너뛰고 시작 (이미 종료했을 경우)
.\start-servers.ps1 -SkipCheck
```

**예상 출력**:
```
═══════════════════════════════════════════════════════
MOSB Logistics Dashboard - 서버 시작 스크립트 (개선 버전)
═══════════════════════════════════════════════════════

1️⃣  실행 중인 서버 확인 중...

✅ Frontend (포트 3000) 실행 중인 프로세스 없음
✅ 모든 서버 확인 완료

2️⃣  서버 시작 중...

🚀 Frontend 서버 시작 중...
✅ next-env.d.ts 확인 완료 (수정 불필요)
🧹 .next 캐시 정리 중...
✅ .next 캐시 정리 완료
✅ cross-env 확인 완료
✅ Frontend 서버 시작됨 (PID: XXXXX, 새 창에서 실행 중)
   http://localhost:3000
   ⏳ 초기 컴파일 중... (30-60초 소요될 수 있음)
   💡 서버 로그는 새 PowerShell 창에서 확인하세요
✅ Frontend 서버 포트 3000 리스닝 중

═══════════════════════════════════════════════════════
📊 서버 시작 완료
═══════════════════════════════════════════════════════

✅ Frontend: http://localhost:3000
   로그 확인: 새 PowerShell 창

💡 서버 종료:
   - Frontend: 새 PowerShell 창에서 Ctrl+C
   - Backend: Stop-Job -Id XXXXX; Remove-Job -Id XXXXX -Force
```

### 4.2 Step 4: 런타임 검증 체크리스트

#### ✅ Step 4.1: 스크립트 실행 전 확인

- [x] `start-servers.ps1` 파일 존재 확인
- [x] `next-env.d.ts` 파일이 올바른 내용인지 확인 (잘못된 import 없음)
- [x] `package.json`에 `cross-env`가 devDependencies에 포함되어 있는지 확인
- [x] `package.json` dev 스크립트에 `cross-env NODE_ENV=development` 포함 확인

#### Step 4.2: 서버 시작 (자동화됨)

**명령어**:
```powershell
.\start-servers.ps1 -FrontendOnly -CleanCache
```

**확인 항목**:
- [ ] 스크립트가 성공적으로 실행됨
- [ ] `next-env.d.ts` 자동 수정 메시지 없음 (이미 정리됨) 또는 수정 완료 메시지 표시
- [ ] `.next` 캐시 정리 완료 메시지 표시
- [ ] `cross-env` 확인 완료 메시지 표시
- [ ] 새 PowerShell 창이 열리고 `npm run dev` 실행 중
- [ ] 포트 3000 리스닝 메시지 표시 (최대 60초 대기)

#### Step 4.3: 서버 준비 대기 (30-60초)

**확인 방법**:
- 새 PowerShell 창에서 컴파일 진행 상황 확인
- "compiled successfully" 또는 "ready" 메시지 확인
- 포트 3000이 리스닝 상태인지 확인: `Get-NetTCPConnection -LocalPort 3000`

**확인 항목**:
- [ ] 컴파일 완료 메시지 표시
- [ ] "ready on http://localhost:3000" 메시지 표시
- [ ] JavaScript/TypeScript 오류 없음

#### Step 4.4: 브라우저 접근 검증

**4.4.1 루트 페이지 (`/`)**:
- [ ] `http://localhost:3000/` 접속
- [ ] 페이지 정상 로드 (JSX 오류 없음)
- [ ] 브라우저 콘솔 (F12)에서 JavaScript 오류 없음
- [ ] `jsxDEV is not a function` 오류 없음

**4.4.2 Client-Only Dashboard (`/dashboard-client-only`)**:
- [ ] `http://localhost:3000/dashboard-client-only` 접속
- [ ] 로그인 화면 또는 "Authenticating..." 메시지 표시
- [ ] 브라우저 콘솔에서 JavaScript 오류 없음
- [ ] 404 오류 없음 (라우트 정상 컴파일됨)

#### Step 4.5: 인증 및 초기 데이터 로딩

**4.5.1 로그인 테스트**:
- [ ] 로그인 폼 표시
- [ ] 데모 사용자 안내 메시지 표시 ("Demo users: ops_user/ops123, finance_user/finance123, ...")
- [ ] `ops_user / ops123`로 로그인 시도
- [ ] 로그인 성공 후 대시보드 화면 표시
- [ ] 상단 헤더에 "User: ops_user (OPS)" 표시
- [ ] Logout 버튼 표시

**4.5.2 초기 데이터 로딩 (Network 탭 확인)**:
브라우저 개발자 도구 (F12) → Network 탭:
- [ ] `GET /api/locations` → 200 OK, 8개 locations
- [ ] `GET /api/legs` → 200 OK, 6개 legs
- [ ] `GET /api/events` → 200 OK, 28개 이상 events
- [ ] `GET /data/geofence.json` → 200 OK, JSON 파싱 성공
- [ ] JavaScript 오류 없음 (콘솔 확인)

#### Step 4.6: 지도 렌더링 검증

- [ ] 지도가 화면에 표시됨 (MapLibre 베이스맵)
- [ ] 다크 테마 스타일 적용 (Carto Dark Matter)
- [ ] 아부다비 근처 지역 표시 (초기 뷰포트: 24.3°N, 54.3°E, zoom 10)
- [ ] 지오펜스 아웃라인 표시 (8개 폴리곤, GeoJsonLayer)
- [ ] 이벤트 포인트 표시 (ScatterplotLayer, enter/exit 색상)
  - [ ] 초록색 포인트: `enter` 이벤트
  - [ ] 빨간색 포인트: `exit` 이벤트
  - [ ] 파란색 포인트: `move` 이벤트
- [ ] Legs 아크 표시 (6개, ArcLayer, ROAD/SEA 색상 구분)
- [ ] 위치 라벨 표시 (TextLayer, 8개 위치 이름)

#### Step 4.7: KPI 패널 검증

- [ ] "Shipments: X" (X > 0, 이벤트에서 파생된 shipment 수)
- [ ] "Planned: X" 표시
- [ ] "In-Transit: X" 표시
- [ ] "Arrived: X" 표시
- [ ] "Delayed: X" 표시
- [ ] "Hold: X" 표시
- [ ] "Unknown: X" 표시
- [ ] "Events in window: X" (X ≥ 28, 시간 윈도우 내 이벤트 수)

#### Step 4.8: WebSocket 연결 검증

**브라우저 개발자 도구 (F12) → Network 탭 → WS 필터**:
- [ ] `ws://localhost:8000/ws/events` 연결 성공
- [ ] `hello` 메시지 수신 (연결 시, `{type: "hello"}`)
- [ ] `ping` 메시지 주기적 수신 (10초마다, `{type: "ping"}`)

**실시간 이벤트 테스트**:
- [ ] 별도 터미널에서 `POST /api/events/demo` 실행:
  ```powershell
  # 로그인하여 토큰 획득
  $response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" `
    -Method POST -ContentType "application/json" `
    -Body '{"username":"ops_user","password":"ops123"}'
  $token = $response.access_token

  # Demo 이벤트 생성
  Invoke-RestMethod -Uri "http://localhost:8000/api/events/demo" `
    -Method POST -Headers @{Authorization="Bearer $token"}
  ```
- [ ] 대시보드에서 새 이벤트 포인트 즉시 표시 (500ms 배치 후)
- [ ] "Events in window" 카운트 증가

#### Step 4.9: UI 컨트롤 검증

**레이어 토글**:
- [ ] Geofence mask 체크/해제 → 지오펜스 영역 마스킹 토글 (MaskExtension)
- [ ] Heatmap 체크/해제 → 히트맵 레이어 표시/숨김 (HeatmapLayer)
- [ ] ETA wedge 체크/해제 → ETA 3D 웨지 표시/숨김 (SolidPolygonLayer)

**시간 윈도우 조절**:
- [ ] 12시간으로 변경 → 오래된 이벤트 제거 (슬라이딩 윈도우)
- [ ] 48시간으로 변경 → 더 많은 이벤트 표시
- [ ] "Events in window" 카운트 업데이트

**히트맵 필터**:
- [ ] "enter" 선택 → enter 이벤트만 히트맵에 표시
- [ ] "exit" 선택 → exit 이벤트만 히트맵에 표시
- [ ] "all" 선택 → 모든 이벤트 히트맵에 표시

#### Step 4.10: 지도 인터랙션 검증

- [ ] 마우스 휠로 확대/축소 동작 (MapLibre + DeckGL 동기화)
- [ ] 마우스 드래그로 지도 이동 (MapLibre + DeckGL 동기화)
- [ ] DeckGL 레이어가 MapLibre와 동기화 (뷰포트 변경 시)
  - [ ] 이벤트 포인트가 베이스맵과 함께 이동
  - [ ] 히트맵이 베이스맵과 함께 이동
  - [ ] 아크 레이어가 베이스맵과 함께 이동
  - [ ] 지오펜스 아웃라인이 베이스맵과 함께 이동
- [ ] 지오펜스 판정 색상 정확성:
  - [ ] 초록색 포인트: `enter` 이벤트 (지오펜스 진입)
  - [ ] 빨간색 포인트: `exit` 이벤트 (지오펜스 이탈)
  - [ ] 파란색 포인트: `move` 이벤트 (지오펜스 내 이동)

#### Step 4.11: 성능 검증

**브라우저 개발자 도구 (F12) → Performance 탭**:
- [ ] 초기 로딩 시간 < 5초
- [ ] 이벤트 업데이트 시 프레임 드롭 없음 (60 FPS 유지)
- [ ] 메모리 사용량 안정적 (< 500MB 권장)
- [ ] 10분간 대시보드 유지 후 메모리 누수 확인

#### Step 4.12: 오류 처리 검증

**백엔드 서버 다운 시나리오**:
- [ ] 백엔드 서버 종료 (PowerShell: `Get-Job | Stop-Job; Get-Job | Remove-Job -Force`)
- [ ] WebSocket 연결 종료 감지 (브라우저 콘솔 확인)
- [ ] 자동 재연결 시도 (백오프: 500ms → 1s → 2s → ... → 10s)
- [ ] 백엔드 서버 재시작: `.\start-servers.ps1 -BackendOnly`
- [ ] 재연결 성공 시 정상 동작 재개

**네트워크 오류 시나리오**:
- [ ] 브라우저 개발자 도구 → Network 탭 → Offline 체크
- [ ] WebSocket 연결 종료 감지
- [ ] 재연결 시도 (최대 10초 백오프)
- [ ] Network 탭 → Offline 체크 해제
- [ ] 네트워크 복구 시 자동 재연결

**인증 토큰 만료 시나리오**:
- [ ] 토큰 만료 후 API 호출 (30분 후)
- [ ] 401 Unauthorized 응답
- [ ] 자동 로그아웃
- [ ] 로그인 화면으로 리다이렉트

### 4.3 검증 결과 요약

**완료된 항목** ✅:
- [x] `start-servers.ps1` 스크립트 개선 완료
  - [x] 자동 `next-env.d.ts` 수정 기능
  - [x] 자동 `.next` 캐시 정리 기능 (`-CleanCache`)
  - [x] 프론트엔드 서버를 새 PowerShell 창에서 실행
  - [x] 글로벌 `NODE_ENV=production` 자동 감지 및 제거
  - [x] `cross-env` 자동 설치 확인 및 설치
  - [x] 백엔드 Job 스코프 환경 변수 전달 개선
  - [x] PowerShell Jobs 정리 기능 강화
  - [x] 백엔드 Job ID 추적
- [x] JSX 런타임 오류 해결 완료
- [x] TypeScript 컴파일 성공
- [x] Next.js 빌드 성공
- [x] 백엔드 서버 실행 성공
- [x] 프론트엔드 서버 실행 성공
- [x] 백엔드 API 엔드포인트 검증 완료

**수동 검증 필요 항목** ⚠️:
- [ ] Step 4.4 ~ Step 4.12 모든 체크리스트 항목

---

## 다음 단계 (업데이트: 2026-01-10)

### ✅ 즉시 완료된 작업

1. **✅ `start-servers.ps1` 스크립트 개선 완료**
   - 자동 `next-env.d.ts` 수정
   - 자동 `.next` 캐시 정리 (`-CleanCache` 옵션)
   - 프론트엔드 서버를 새 PowerShell 창에서 실행
   - 글로벌 `NODE_ENV=production` 자동 감지 및 제거
   - `cross-env` 자동 설치 확인 및 설치
   - 백엔드 Job 스코프 환경 변수 전달 개선
   - PowerShell Jobs 정리 기능 강화
   - 백엔드 Job ID 추적

2. **✅ JSX 런타임 오류 해결 완료**
   - 글로벌 `NODE_ENV=production` 제거 (자동화됨)
   - `package.json`에 `cross-env NODE_ENV=development` 추가
   - `next-env.d.ts`에서 잘못된 import 제거 (자동화됨)
   - `tsconfig.json` `jsx: "react-jsx"` 설정 확인
   - `.next` 캐시 정리 (자동화됨)

### ⚠️ 다음 실행 단계 (수동)

**Step 4: 런타임 검증 실행**:

1. **서버 시작**:
   ```powershell
   .\start-servers.ps1 -FrontendOnly -CleanCache
   ```

2. **서버 준비 대기** (30-60초):
   - 새 PowerShell 창에서 컴파일 완료 확인
   - "ready" 또는 "compiled successfully" 메시지 확인

3. **브라우저 테스트**:
   - `http://localhost:3000/dashboard-client-only` 접속
   - 위의 "Step 4: 런타임 검증 체크리스트" 항목 확인

4. **검증 결과 기록**:
   - 체크리스트 항목별 결과 기록
   - 발견된 이슈 또는 개선 사항 문서화

### 후속 작업

1. **검증 결과 업데이트**:
   - 브라우저 테스트 완료 후 이 문서 업데이트
   - 발견된 버그 또는 개선 사항 기록

2. **프로덕션 준비**:
   - 환경 변수 설정 확인
   - 성능 최적화 확인
   - 보안 설정 확인

---

**문서 버전**: 1.1
**최종 업데이트**: 2026-01-10 (Step 4 런타임 검증 절차 추가)
