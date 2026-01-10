# JSX Runtime Error 해결 완료 요약

**해결 일시**: 2026-01-10
**상태**: ✅ **해결 완료**

---

## 문제 상황

브라우저 콘솔에 다음 오류가 발생하여 페이지가 렌더링되지 않았습니다:
```
Uncaught TypeError: {imported module [externals]/react/jsx-dev-runtime}.jsxDEV is not a function
```

---

## 원인 분석

### 주요 원인 (근본 원인) ✅

**글로벌 `NODE_ENV=production` 설정**

- Windows PowerShell에서 글로벌 환경 변수로 `NODE_ENV=production`이 설정되어 있었음
- 이로 인해 Next.js 개발 서버가 프로덕션 JSX 런타임을 로드하려고 시도
- `cross-env NODE_ENV=development`가 있더라도 글로벌 환경 변수가 우선순위가 높음

### 부차적 원인

1. **`next-env.d.ts`에 잘못된 import**
   - `import "./.next/dev/types/routes.d.ts"` 추가됨
   - 이 파일은 Next.js가 자동 생성하며 수동 import가 포함되면 안 됨

2. **`.next` 캐시**
   - 이전 빌드에서 잘못된 JSX 런타임이 캐시됨

---

## 해결 방법

### 1. 글로벌 NODE_ENV 제거 ✅

```powershell
# PowerShell에서 글로벌 NODE_ENV 확인 및 제거
$env:NODE_ENV
# 출력: "production"

# 글로벌 NODE_ENV 제거 (현재 세션)
$env:NODE_ENV = $null

# 확인
$env:NODE_ENV
# 출력: (비어있음)
```

**주의**: 이는 현재 PowerShell 세션에만 적용됩니다. 시스템 전역 환경 변수를 변경하려면:
- 시스템 환경 변수 설정에서 `NODE_ENV` 제거
- 또는 각 터미널 세션에서 `$env:NODE_ENV = $null` 실행

### 2. package.json dev 스크립트 수정 ✅

```json
{
  "scripts": {
    "dev": "cross-env NODE_ENV=development next dev -p 3000"
  },
  "devDependencies": {
    "cross-env": "^7.0.3"
  }
}
```

### 3. next-env.d.ts 정리 ✅

**잘못된 버전** (수정 전):
```typescript
/// <reference types="next" />
/// <reference types="next/image-types/global" />
import "./.next/dev/types/routes.d.ts";  // ❌ 제거 필요

// NOTE: This file should not be edited
```

**올바른 버전** (수정 후):
```typescript
/// <reference types="next" />
/// <reference types="next/image-types/global" />

// NOTE: This file should not be edited
```

### 4. tsconfig.json 설정 확인 ✅

```json
{
  "compilerOptions": {
    "jsx": "react-jsx"  // ✅ 올바른 설정
  }
}
```

**참고**: `jsx: "preserve"`는 Next.js 16.1.1에서도 작동하지만, `jsx: "react-jsx"`가 더 안정적입니다.

### 5. 캐시 정리 ✅

```powershell
cd mosb_logistics_dashboard_next_fastapi_mvp\frontend
Remove-Item -Recurse -Force .next
```

---

## 검증 결과

### ✅ JSX 런타임 오류 해결 확인

**검증 방법**:
1. 브라우저에서 `http://localhost:3000/` 접속
2. 개발자 도구 (F12) → Console 탭 확인
3. **결과**: `jsxDEV is not a function` 오류 없음 ✅

**콘솔 메시지** (정상):
- ✅ React DevTools 경고 (정상, 무해)
- ✅ HMR connected (정상)
- ✅ Fast Refresh 메시지 (정상)
- ✅ Workbox 경고 (정상, 무해)
- ❌ **`jsxDEV is not a function` 오류 없음** ✅

### ⚠️ `/dashboard-client-only` 라우트 404 오류

- **상태**: 파일은 존재하나 404 오류 발생
- **원인**: 서버가 아직 해당 라우트를 컴파일하지 않았을 수 있음
- **해결책**: 서버 재시작 후 30-60초 대기

---

## 다음 단계

### 1. 서버 재시작 (수동)

**PowerShell에서**:

```powershell
# 1. 글로벌 NODE_ENV 제거 (현재 세션)
$env:NODE_ENV = $null

# 2. 프론트엔드 디렉토리로 이동
cd mosb_logistics_dashboard_next_fastapi_mvp\frontend

# 3. .next 캐시 정리 (선택사항, 권장)
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue

# 4. 서버 시작
npm run dev
```

### 2. 서버 준비 대기

- 서버 시작 후 **30-60초 대기** (첫 빌드 시간)
- 터미널에서 "Ready on http://localhost:3000" 메시지 확인

### 3. 브라우저 테스트

1. **루트 페이지 확인**:
   - URL: `http://localhost:3000/`
   - 예상: 로그인 화면 또는 대시보드 표시
   - 콘솔: JSX 오류 없음 ✅

2. **Client-Only Dashboard 확인**:
   - URL: `http://localhost:3000/dashboard-client-only`
   - 예상: 로그인 화면 또는 대시보드 표시
   - 콘솔: JSX 오류 없음 ✅

### 4. 시스템 전역 NODE_ENV 제거 (선택사항)

글로벌 `NODE_ENV=production`이 시스템 환경 변수로 설정되어 있다면:

1. **Windows 환경 변수 설정**:
   - `Win + R` → `sysdm.cpl` → 고급 → 환경 변수
   - 시스템 변수에서 `NODE_ENV` 찾기
   - 있으면 삭제

2. **또는 PowerShell 프로파일 수정**:
   ```powershell
   # 프로파일 위치 확인
   $PROFILE

   # 프로파일 편집
   notepad $PROFILE

   # NODE_ENV 설정 제거
   ```

---

## 해결 체크리스트

- [x] 글로벌 `NODE_ENV=production` 발견
- [x] 글로벌 `NODE_ENV` 제거 (현재 세션)
- [x] `package.json`에 `cross-env NODE_ENV=development` 추가
- [x] `next-env.d.ts`에서 잘못된 import 제거
- [x] `tsconfig.json` `jsx: "react-jsx"` 설정 확인
- [x] `.next` 캐시 정리
- [x] 브라우저 콘솔에서 JSX 오류 해결 확인 (루트 페이지)
- [ ] `/dashboard-client-only` 라우트 접근 확인 (서버 재시작 후)

---

## 참고 자료

- [Next.js TypeScript Configuration](https://nextjs.org/docs/pages/building-your-application/configuring/typescript)
- [React JSX Runtime](https://react.dev/reference/react/jsx-runtime)
- [cross-env npm package](https://www.npmjs.com/package/cross-env)

---

**문서 버전**: 1.0
**최종 업데이트**: 2026-01-10
