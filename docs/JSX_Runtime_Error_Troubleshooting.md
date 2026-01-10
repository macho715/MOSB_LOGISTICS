# JSX Runtime Error Troubleshooting Guide

**작성일**: 2026-01-10
**오류**: `Uncaught TypeError: {imported module [externals]/react/jsx-dev-runtime}.jsxDEV is not a function`

---

## 문제 상황

브라우저 콘솔에 JSX 런타임 오류가 발생하여 페이지가 렌더링되지 않습니다.

**오류 메시지**:
```
Uncaught TypeError: {imported module [externals]/react/jsx-dev-runtime}.jsxDEV is not a function
```

---

## 이미 시도한 해결 방법 ✅

### 1. `next-env.d.ts` 정리 ✅
- **상태**: 완료
- **작업**: 잘못된 import 제거 (`import "./.next/dev/types/routes.d.ts"`)
- **결과**: 오류 지속

### 2. `.next` 캐시 정리 ✅
- **상태**: 완료
- **작업**: `rm -rf .next` 실행
- **결과**: 오류 지속

### 3. 완전 재설치 ✅
- **상태**: 완료
- **작업**: `rm -rf node_modules .next package-lock.json && npm install`
- **결과**: 오류 지속

### 4. `tsconfig.json` 설정 확인 ✅
- **상태**: 완료
- **현재 설정**: `jsx: "preserve"` (Next.js 16.1.1 권장)
- **결과**: 오류 지속

### 5. React 버전 확인 ✅
- **상태**: 완료
- **설치된 버전**: `react@18.2.0`, `react-dom@18.2.0`
- **중복 확인**: 단일 복사본 (deduped)
- **결과**: 오류 지속

---

## 현재 환경

- **Next.js**: 16.1.1
- **React**: 18.2.0
- **React-DOM**: 18.2.0
- **TypeScript**: 5.9.3
- **tsconfig.json**: `jsx: "preserve"`

---

## 추가 시도 가능한 해결 방법

### 방법 1: Next.js 버전 다운그레이드 (권장)

Next.js 16.1.1에 알려진 이슈가 있을 수 있습니다. 안정 버전으로 다운그레이드:

```bash
cd mosb_logistics_dashboard_next_fastapi_mvp/frontend
npm install next@15.1.0 react@18.2.0 react-dom@18.2.0
rm -rf .next
npm run dev
```

### 방법 2: React 버전 업그레이드

React 18.3.x로 업그레이드 (최신 18.x 안정 버전):

```bash
cd mosb_logistics_dashboard_next_fastapi_mvp/frontend
npm install react@18.3.1 react-dom@18.3.1
rm -rf .next node_modules package-lock.json
npm install
npm run dev
```

### 방법 3: tsconfig.json을 `react-jsx`로 변경

Next.js 16.1.1이 `jsx: "preserve"`와 호환되지 않을 수 있습니다:

```json
{
  "compilerOptions": {
    "jsx": "react-jsx"
  }
}
```

그 후:
```bash
rm -rf .next
npm run dev
```

### 방법 4: next.config.js에 명시적 설정 추가

```js
module.exports = {
  reactStrictMode: true,
  compiler: {
    reactRemoveProperties: false,
  },
  swcMinify: true,
  experimental: {
    forceSwcTransforms: true,
  },
};
```

### 방법 5: Next.js 이슈 확인

1. Next.js GitHub 이슈 트래커 확인:
   - https://github.com/vercel/next.js/issues?q=jsxDEV+is+not+a+function
   - Next.js 16.1.1 알려진 이슈 검색

2. Stack Overflow 검색:
   - "Next.js 16 jsxDEV not a function"
   - "Next.js 16.1.1 React 18.2 JSX runtime error"

### 방법 6: 프로덕션 빌드 테스트

개발 모드와 프로덕션 모드의 차이 확인:

```bash
cd mosb_logistics_dashboard_next_fastapi_mvp/frontend
npm run build
npm start
```

프로덕션 빌드에서 오류가 없으면 개발 모드 특정 이슈일 수 있습니다.

### 방법 7: 다른 Next.js 프로젝트와 비교

정상 작동하는 Next.js 16 프로젝트의 설정 비교:
- `tsconfig.json` 비교
- `next.config.js` 비교
- `package.json` 의존성 버전 비교

---

## 진단 명령어

### React JSX Runtime 확인

```bash
cd mosb_logistics_dashboard_next_fastapi_mvp/frontend
node -e "const rt = require('react/jsx-dev-runtime'); console.log('jsxDEV type:', typeof rt.jsxDEV); console.log('jsxDEV value:', rt.jsxDEV); console.log('Exports:', Object.keys(rt));"
```

**예상 결과** (정상):
```
jsxDEV type: function
jsxDEV value: [Function: jsxWithValidation]
Exports: [ 'Fragment', 'jsxDEV' ]
```

**현재 결과** (오류):
```
jsxDEV type: undefined
jsxDEV value: undefined
Exports: [ 'Fragment', 'jsxDEV' ]
```

### Next.js 버전 확인

```bash
cd mosb_logistics_dashboard_next_fastapi_mvp/frontend
npx next --version
```

### 의존성 중복 확인

```bash
cd mosb_logistics_dashboard_next_fastapi_mvp/frontend
npm ls react react-dom next
```

**정상**: 모든 패키지가 단일 복사본 (deduped)
**문제**: 여러 버전이 혼재

---

## 임시 우회 방법

JSX 오류 해결 전까지 임시로 사용 가능한 대안:

### 1. 기존 대시보드 사용
- URL: `http://localhost:3000/` (기존 `index.tsx`)
- Client-Only Dashboard가 아닌 기존 대시보드 사용

### 2. 프로덕션 빌드 사용
- 개발 모드 대신 프로덕션 빌드 사용 (오류가 없을 수 있음)
- `npm run build && npm start`

---

## 권장 해결 순서

1. **Next.js 버전 다운그레이드** (가장 빠른 해결책)
   - Next.js 15.1.0으로 다운그레이드
   - 안정성이 검증된 버전

2. **React 버전 업그레이드**
   - React 18.3.1로 업그레이드
   - Next.js 16.1.1과의 호환성 개선 가능

3. **tsconfig.json 변경**
   - `jsx: "react-jsx"`로 변경
   - TypeScript가 JSX를 직접 변환

4. **Next.js 이슈 트래커 확인**
   - 알려진 이슈 및 해결책 확인
   - 커뮤니티 해결책 적용

---

## 참고 자료

- [Next.js TypeScript Configuration](https://nextjs.org/docs/pages/building-your-application/configuring/typescript)
- [Next.js 16.1.1 Release Notes](https://github.com/vercel/next.js/releases/tag/v16.1.1)
- [React JSX Runtime](https://react.dev/reference/react/jsx-runtime)
- [Next.js GitHub Issues](https://github.com/vercel/next.js/issues)

---

**문서 버전**: 1.0
**최종 업데이트**: 2026-01-10
