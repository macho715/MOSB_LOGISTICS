# 서버 확인 및 재시작 스크립트 (개선 버전)

Windows 환경에서 로컬 개발 서버(Backend/Frontend)를 확인하고 재시작하는
`start-servers.ps1` 스크립트를 제공합니다. 기본 동작은 포트 8000/3000에서
실행 중인 프로세스를 종료한 뒤, 각 서버를 재시작합니다.

**개선 사항 (2026-01-10)**:
- ✅ `next-env.d.ts` 자동 수정 (잘못된 import 제거, Windows/Unix 줄바꿈 모두 지원)
- ✅ `.next` 캐시 정리 옵션 (`-CleanCache`)
- ✅ 프론트엔드 서버를 새 PowerShell 창에서 실행 (로그 확인 가능)
- ✅ 글로벌 `NODE_ENV=production` 자동 제거
- ✅ `cross-env` 자동 설치 확인 (package.json 및 node_modules 모두 확인)
- ✅ 서버 상태 확인 개선 (포트 리스닝 확인, 최대 60초 대기)
- ✅ Backend Job 스코프 격리 문제 해결 (환경 변수 올바른 전달)
- ✅ 포트 정리 개선 (PowerShell Jobs도 함께 정리, 최대 5초 대기)
- ✅ Backend Job ID 추적 및 보고 (종료 명령어 자동 생성)

## 사용 방법

```powershell
# 두 서버 모두 시작 (기본)
.\start-servers.ps1

# Backend만 시작
.\start-servers.ps1 -BackendOnly

# Frontend만 시작 (캐시 정리 포함)
.\start-servers.ps1 -FrontendOnly -CleanCache

# 캐시 정리 후 시작
.\start-servers.ps1 -CleanCache

# 서버 확인 없이 바로 시작
.\start-servers.ps1 -SkipCheck
```

## 주요 기능

### 1. 자동 파일 수정
- `next-env.d.ts`에 잘못된 import가 있으면 자동으로 제거
- Windows/Unix 줄바꿈 모두 지원, 빈 줄 정리 포함
- JSX 런타임 오류 방지

### 2. 캐시 관리
- `-CleanCache` 옵션으로 `.next` 캐시 자동 정리
- 빌드 문제 해결에 유용

### 3. 프론트엔드 서버 실행 개선
- 새 PowerShell 창에서 실행되어 로그 확인 가능
- `cross-env` 자동 설치 확인 (`package.json` 및 `node_modules` 모두 확인)
- 글로벌 `NODE_ENV=production` 자동 제거
- 환경 변수 자동 설정 및 검증

### 4. 백엔드 서버 실행 개선
- PowerShell Job 스코프 격리 문제 해결
- `.env` 파일 파싱 및 환경 변수 올바른 전달
- Backend Job ID 추적 및 보고

### 5. 서버 종료 및 정리
- 포트 사용 중인 프로세스 자동 감지 및 종료
- PowerShell Jobs도 함께 정리 (orphaned processes 방지)
- 포트 해제 대기 (최대 5초, 재시도 포함)
- 종료 명령어 자동 생성 및 안내

### 6. 서버 상태 확인
- 포트 리스닝 상태 확인 (최대 60초 대기)
- 서버 준비 완료 시 알림
- Backend Job 상태 확인 및 보고
