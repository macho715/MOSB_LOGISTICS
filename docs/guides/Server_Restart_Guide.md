# 서버 재시작 가이드

**작성일**: 2026-01-10
**이유**: `next-env.d.ts` 파일 수정 후 변경 사항 반영

---

## 문제 상황

브라우저 콘솔에 다음 오류가 발생:
```
Uncaught TypeError: {imported module [externals]/react/jsx-dev-runtime}.jsxDEV is not a function
```

**원인**: `next-env.d.ts` 파일에 잘못된 import가 포함되어 있었음

**해결**: 파일에서 잘못된 import 제거 완료 (`import "./.next/dev/types/routes.d.ts"` 삭제)

---

## 재시작 절차

### 1. 현재 실행 중인 서버 종료

**PowerShell에서**:
```powershell
# 프론트엔드 서버 종료 (포트 3000)
Get-Process -Id 34204 -ErrorAction SilentlyContinue | Stop-Process -Force

# 또는 포트 3000 사용 프로세스 직접 종료
$proc = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($proc) { Stop-Process -Id $proc -Force }
```

**또는 간단하게**:
- 프론트엔드 서버 실행 중인 터미널에서 `Ctrl+C` 입력

### 2. .next 캐시 정리 (선택사항, 권장)

```powershell
cd mosb_logistics_dashboard_next_fastapi_mvp/frontend
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
```

### 3. 프론트엔드 서버 재시작

```powershell
cd mosb_logistics_dashboard_next_fastapi_mvp/frontend
npm run dev
```

### 4. 서버 준비 대기

서버 시작 후 30-60초 대기 (첫 빌드 시간)

### 5. 브라우저에서 확인

- URL: `http://localhost:3000/dashboard-client-only`
- 브라우저 콘솔 확인 (F12):
  - ✅ JSX 런타임 오류 없음
  - ✅ 페이지 정상 렌더링
  - ⚠️ 경고만 있고 오류 없음

---

## 백엔드 서버 상태 확인

백엔드 서버는 정상 실행 중 (포트 8000):
- **프로세스 ID**: 39848
- **API 엔드포인트**: 모두 정상 동작 확인
- **재시작 불필요**

---

## 예상 결과

서버 재시작 후:
1. ✅ JSX 런타임 오류 해결
2. ✅ 로그인 화면 정상 표시
3. ✅ 대시보드 페이지 정상 렌더링
4. ✅ 지도 컴포넌트 정상 로드

---

## 문제가 계속되는 경우

1. **node_modules 재설치**:
   ```powershell
   cd mosb_logistics_dashboard_next_fastapi_mvp/frontend
   Remove-Item -Recurse -Force node_modules .next package-lock.json
   npm install
   npm run dev
   ```

2. **React 버전 확인**:
   ```powershell
   npm ls react react-dom
   ```
   - 예상: `react@18.2.0`, `react-dom@18.2.0` (단일 복사본)

3. **브라우저 캐시 클리어**:
   - `Ctrl+Shift+Delete` → 캐시된 이미지 및 파일 삭제
   - 또는 `Ctrl+F5` (강력 새로고침)

---

**문서 버전**: 1.0
**최종 업데이트**: 2026-01-10
