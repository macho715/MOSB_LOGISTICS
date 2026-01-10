# Client-Only Dashboard 사용 가이드

**작성일**: 2026-01-10
**버전**: 1.0

---

## 개요

Client-Only Dashboard는 모든 도메인 로직(지오펜스 필터링, 히트맵 집계, ETA 계산)을 브라우저에서 수행하는 대시보드입니다. 서버 부하를 최소화하고 빠른 프로토타이핑을 가능하게 합니다.

**접근 경로**: `http://localhost:3000/dashboard-client-only`

---

## 기능

### 1. 지도 시각화

#### 레이어
- **지오펜스 아웃라인**: 위치별 경계 표시 (MOSB/WH/PORT/BERTH/SITE)
- **이벤트 포인트**: 실시간 이벤트 위치 표시
  - 초록색: `enter` 이벤트 (지오펜스 진입)
  - 빨간색: `exit` 이벤트 (지오펜스 이탈)
  - 파란색: `move` 이벤트 (일반 이동)
- **Arc 레이어**: Legs 시각화 (운송 구간)
- **위치 라벨**: 각 위치의 이름 표시
- **히트맵**: 이벤트 밀도 시각화 (상태 기반 가중치)
- **ETA Wedge**: 예상 도착 시간 범위 시각화 (3D 폴리곤)

### 2. KPI 패널

상단 패널에서 다음 지표를 확인할 수 있습니다:
- **Shipments**: 전체 shipment 수
- **Planned**: 계획된 shipment 수
- **In-Transit**: 운송 중인 shipment 수
- **Arrived**: 도착한 shipment 수
- **Delayed**: 지연된 shipment 수
- **Hold**: 보류된 shipment 수
- **Unknown**: 상태 불명 shipment 수
- **Events in window**: 현재 시간 윈도우 내 이벤트 수

### 3. 레이어 토글

- **Geofence mask**: 지오펜스 마스킹 활성화/비활성화
- **Heatmap**: 히트맵 레이어 표시/숨김
- **ETA wedge**: ETA wedge 레이어 표시/숨김

### 4. 필터 및 설정

- **Window (hours)**: 시간 윈도우 조절 (1-168시간, 기본 24시간)
- **Heat filter**: 히트맵 필터 (all/enter/exit/move/unknown)

---

## 사용 방법

### 1. 로그인

1. `http://localhost:3000/dashboard-client-only` 접속
2. 데모 사용자로 로그인:
   - `ops_user / ops123` (OPS)
   - `finance_user / finance123` (FINANCE)
   - `compliance_user / compliance123` (COMPLIANCE)
   - `admin / admin123` (ADMIN)

### 2. 지도 탐색

- **확대/축소**: 마우스 휠 또는 핀치 제스처
- **이동**: 마우스 드래그
- **회전**: Ctrl + 드래그 (MapLibre 컨트롤)
- **기울기**: Shift + 드래그 (MapLibre 컨트롤)

### 3. 레이어 제어

상단 패널의 체크박스로 레이어를 켜고 끌 수 있습니다:
- 지오펜스 마스킹: 이벤트를 지오펜스 내부만 표시
- 히트맵: 이벤트 밀도 시각화
- ETA wedge: 예상 도착 시간 범위

### 4. 시간 윈도우 조절

"Window (hours)" 입력 필드에서 시간 범위를 조절합니다:
- 기본값: 24시간
- 범위: 1-168시간 (1주)
- 슬라이딩 윈도우로 오래된 이벤트 자동 제거

---

## 개발자 가이드

### 아키텍처

```
┌─────────────────────────────────────────┐
│  WebSocket (FastAPI)                    │
│  {type: "event", payload: {...}}        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  useBatchedClientOnlyWs (500ms batch)   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  useClientOnlyStore (Zustand)           │
│  - ingestEvents()                       │
│  - deriveShipmentsFromEvents()          │
│  - pruneOldEvents()                     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  ClientOnlyMap (DeckGL + MapLibre)      │
│  - Geofence 판정 (BBox + Turf)          │
│  - Heatmap 집계                         │
│  - ETA 계산                             │
└─────────────────────────────────────────┘
```

### 주요 파일

- **상태 관리**: `store/useClientOnlyStore.ts`
- **지도 컴포넌트**: `components/client-only/ClientOnlyMap.tsx`
- **대시보드 UI**: `components/client-only/ClientOnlyDashboard.tsx`
- **지오펜스 유틸**: `lib/client-only/geofence.ts`
- **히트맵 유틸**: `lib/client-only/heatmap.ts`
- **ETA 유틸**: `lib/client-only/eta.ts`
- **WebSocket 파서**: `lib/client-only/ws.ts`

### 데이터 흐름

1. **초기 로딩**: REST API로 Locations, Legs, Events 로드
2. **실시간 업데이트**: WebSocket으로 이벤트 수신 (500ms 배치)
3. **지오펜스 판정**: 각 이벤트의 위치를 지오펜스와 비교
4. **Shipment 파생**: 최신 이벤트에서 shipment 상태/위치 파생
5. **히트맵 집계**: 시간 윈도우 내 이벤트를 그리드로 집계
6. **ETA 계산**: Legs와 현재 위치에서 ETA 범위 계산
7. **렌더링**: DeckGL 레이어로 시각화

---

## 문제 해결

### 문제 1: 지도가 표시되지 않음

**증상**: 빈 화면 또는 에러 메시지

**해결책**:
1. 브라우저 콘솔 확인 (F12)
2. MapLibre 스타일 URL 확인: `https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json`
3. 네트워크 탭에서 스타일 로드 확인
4. CORS 오류 확인

### 문제 2: 이벤트가 표시되지 않음

**증상**: 지도에 이벤트 포인트가 없음

**해결책**:
1. WebSocket 연결 확인 (상단 패널의 "Events in window" 확인)
2. 브라우저 콘솔에서 WebSocket 오류 확인
3. 백엔드 서버 실행 확인 (`http://localhost:8000`)
4. 인증 토큰 확인 (localStorage)

### 문제 3: 지오펜스가 표시되지 않음

**증상**: 지오펜스 아웃라인이 보이지 않음

**해결책**:
1. `public/data/geofence.json` 파일 존재 확인
2. 브라우저 콘솔에서 GeoJSON 로드 오류 확인
3. JSON 형식 유효성 확인 (https://jsonlint.com)
4. 좌표 순서 확인 (`[lng, lat]`)

### 문제 4: 히트맵이 표시되지 않음

**증상**: 히트맵 레이어가 비어있음

**해결책**:
1. "Heatmap" 체크박스 활성화 확인
2. 시간 윈도우 내 이벤트 존재 확인
3. iOS Safari인 경우: 가중치 범위 확인 (1-255)
4. 브라우저 콘솔에서 WebGL 오류 확인

### 문제 5: 성능 저하

**증상**: 지도가 느리거나 브라우저가 멈춤

**해결책**:
1. 이벤트 수 확인 (상단 패널의 "Events in window")
2. 시간 윈도우 축소 (예: 12시간)
3. 불필요한 레이어 비활성화
4. 브라우저 개발자 도구에서 메모리 사용량 확인

---

## 성능 최적화

### 권장 설정

- **시간 윈도우**: 24시간 (기본값)
- **최대 이벤트 수**: 1000개 (자동 제한)
- **배치 처리**: 500ms (기본값)

### 대량 데이터 처리

이벤트가 1000개를 초과하면 자동으로 오래된 이벤트가 제거됩니다 (sliding window). 더 많은 이벤트를 처리하려면:

1. `store/useClientOnlyStore.ts`의 `MAX_EVENTS` 값 조정
2. 메모리 사용량 모니터링
3. 필요시 서버 측 필터링 추가 고려

---

## 보안 고려사항

### Client-Only 특성

- 모든 데이터가 브라우저에 노출됨
- 민감한 정보(PII, BL 번호 등)는 최소화해야 함
- 프로덕션 환경에서는 WSS 사용 필수

### 권장 사항

1. WebSocket 인증 추가 (향후 구현)
2. 민감한 데이터 필터링 (서버 측)
3. HTTPS/WSS 사용 (프로덕션)

---

## 참고 자료

- [지오펜스 데이터 교체 가이드](../frontend/docs/client-only-geofence-guide.md)
- [Deck.gl 문서](https://deck.gl/docs)
- [MapLibre GL JS 문서](https://maplibre.org/maplibre-gl-js-docs/)
- [Turf.js 문서](https://turfjs.org/)

---

**문서 버전**: 1.0
**최종 업데이트**: 2026-01-10
