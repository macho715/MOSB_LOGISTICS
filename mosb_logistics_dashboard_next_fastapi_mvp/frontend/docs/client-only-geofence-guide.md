# Client-Only Dashboard: Geofence 데이터 교체 가이드

**작성일**: 2026-01-10
**버전**: 1.0

---

## 개요

Client-Only Dashboard에서 사용하는 지오펜스 데이터는 `public/data/geofence.json` 파일에 저장되어 있습니다. 현재는 placeholder 데이터(대략적인 사각형 폴리곤)를 사용하고 있으며, 실제 운영 환경에서는 정확한 경계 좌표로 교체해야 합니다.

---

## 현재 데이터 구조

### 파일 위치
- `mosb_logistics_dashboard_next_fastapi_mvp/frontend/public/data/geofence.json`

### 현재 포함된 위치 (8개)
1. **MOSB_ESNAAD** (MOSB) - 중심: 24.328853, 54.45857
2. **DSV_M19** (WH) - 중심: 24.3668127, 54.4764805
3. **MIRFA_ONSHORE** (SITE) - 중심: 24.121, 53.447
4. **SHU_ONSHORE** (SITE) - 중심: 24.156936, 52.569199
5. **AGI_OFFSHORE** (SITE) - 중심: 24.8429, 53.6563
6. **DAS_OFFSHORE** (SITE) - 중심: 25.151385, 52.873894
7. **PORT_MZ** (PORT) - 중심: 24.522483, 54.387718
8. **BERTH_MZ** (BERTH) - 중심: 24.522483, 54.387718

### 현재 좌표 형식
- 각 위치는 중심점 기준 대략적인 사각형 폴리곤 (약 2km × 2km)
- 실제 경계와 다를 수 있음

---

## 실제 데이터 수집 방법

### 방법 1: GPS/측량 데이터 사용
1. 각 위치의 실제 경계 좌표를 GPS 또는 측량 데이터로 수집
2. 좌표계: WGS84 (EPSG:4326) - 경도/위도 순서 `[lng, lat]`
3. 폴리곤은 닫힌 링(closed ring)이어야 함 (첫 점과 마지막 점이 동일)

### 방법 2: 지도 서비스에서 추출
1. Google Maps, OpenStreetMap, 또는 내부 지도 시스템 사용
2. 위치 경계를 그려서 GeoJSON 형식으로 내보내기
3. 좌표 순서 확인: `[lng, lat]` (경도, 위도)

### 방법 3: CAD/GIS 파일 변환
1. CAD 파일(DWG) 또는 GIS 파일(SHP)에서 경계 추출
2. GeoJSON 형식으로 변환 (QGIS, GDAL 등 사용)
3. 좌표계 변환 확인 (WGS84로 변환)

---

## GeoJSON 형식 규칙

### 필수 구조
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": "LOCATION_ID",      // locations.csv의 location_id와 일치
        "kind": "MOSB|SITE|WH|PORT|BERTH",  // locations.csv의 type과 일치
        "name": "Location Name"   // locations.csv의 name과 일치
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [lng1, lat1],  // 첫 점
          [lng2, lat2],
          [lng3, lat3],
          [lng4, lat4],
          [lng1, lat1]   // 닫힌 링 (첫 점과 동일)
        ]]
      }
    }
  ]
}
```

### MultiPolygon 지원
복잡한 형태의 경계는 MultiPolygon도 지원됩니다:
```json
{
  "geometry": {
    "type": "MultiPolygon",
    "coordinates": [
      [[[lng1, lat1], [lng2, lat2], ...]],  // 첫 번째 폴리곤
      [[[lng1, lat1], [lng2, lat2], ...]]  // 두 번째 폴리곤
    ]
  }
}
```

### 좌표 순서 중요
- **GeoJSON 표준**: `[longitude, latitude]` (경도, 위도)
- **주의**: 일반적인 `[lat, lon]` 순서와 반대
- 예: 아부다비 근처 → `[54.45857, 24.328853]` (경도 54.4, 위도 24.3)

---

## 데이터 교체 절차

### Step 1: 실제 좌표 수집
각 위치별로 실제 경계 좌표를 수집합니다.

**권장 도구**:
- GPS 측량 장비
- Google My Maps (폴리곤 그리기)
- QGIS (GIS 소프트웨어)
- 내부 지도 시스템

### Step 2: GeoJSON 형식으로 변환
수집한 좌표를 GeoJSON 형식으로 변환합니다.

**온라인 도구**:
- https://geojson.io (브라우저에서 직접 편집)
- https://mapshaper.org (SHP → GeoJSON 변환)

**프로그래밍 도구**:
- Python: `geopandas`, `shapely`
- Node.js: `@turf/turf`, `geojson`

### Step 3: 파일 교체
1. `public/data/geofence.json` 파일 백업
2. 새로운 GeoJSON 파일로 교체
3. JSON 유효성 검사 (https://jsonlint.com)
4. 좌표 순서 확인 (`[lng, lat]`)

### Step 4: 검증
1. 개발 서버 실행: `npm run dev`
2. `http://localhost:3000/dashboard-client-only` 접속
3. 지도에서 지오펜스 경계 확인
4. 이벤트가 지오펜스 내부/외부 올바르게 판정되는지 확인

---

## 검증 체크리스트

- [ ] JSON 형식 유효성 (JSONLint 통과)
- [ ] 모든 features에 `properties.id` 존재
- [ ] `properties.id`가 `locations.csv`의 `location_id`와 일치
- [ ] `properties.kind`가 `locations.csv`의 `type`과 일치
- [ ] 좌표 순서: `[lng, lat]` (경도, 위도)
- [ ] 폴리곤이 닫힌 링 (첫 점 = 마지막 점)
- [ ] 좌표가 유효한 범위 내 (경도: -180~180, 위도: -90~90)
- [ ] 브라우저에서 지오펜스 경계가 올바르게 표시됨
- [ ] 이벤트 지오펜스 판정이 정확함

---

## 예시: 실제 폴리곤 데이터

### MOSB_ESNAAD 예시 (실제 운영 데이터 필요)
```json
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
      [54.44857, 24.318853],  // 실제 경계 좌표 1
      [54.46857, 24.318853],  // 실제 경계 좌표 2
      [54.46857, 24.338853],  // 실제 경계 좌표 3
      [54.44857, 24.338853],  // 실제 경계 좌표 4
      [54.44857, 24.318853]   // 닫힌 링 (첫 점과 동일)
    ]]
  }
}
```

**참고**: 위 좌표는 placeholder입니다. 실제 운영 데이터로 교체 필요.

---

## 문제 해결

### 문제 1: 지오펜스가 지도에 표시되지 않음
- **원인**: JSON 형식 오류, 좌표 순서 오류
- **해결**: JSONLint로 검증, 좌표 순서 확인 (`[lng, lat]`)

### 문제 2: 이벤트가 지오펜스 내부인데 외부로 판정됨
- **원인**: 좌표 순서 오류 (`[lat, lon]` 대신 `[lng, lat]` 사용)
- **해결**: 좌표 순서 교정

### 문제 3: 폴리곤이 이상하게 표시됨
- **원인**: 좌표가 닫힌 링이 아님, 좌표 순서 반대
- **해결**: 첫 점과 마지막 점이 동일한지 확인, 좌표 순서 확인

---

## 참고 자료

- GeoJSON 스펙: https://geojson.org/
- WGS84 좌표계: https://en.wikipedia.org/wiki/World_Geodetic_System
- deck.gl GeoJsonLayer: https://deck.gl/docs/api-reference/layers/geojson-layer

---

## 연락처

실제 운영 데이터 수집 및 교체는 운영팀과 협의하여 진행하세요.

**문서 버전**: 1.0
**최종 업데이트**: 2026-01-10
