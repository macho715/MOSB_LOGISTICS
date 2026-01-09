# 서버 확인 및 재시작 스크립트

Windows 환경에서 로컬 개발 서버(Backend/Frontend)를 확인하고 재시작하는
`start-servers.ps1` 스크립트를 제공합니다. 기본 동작은 포트 8000/3000에서
실행 중인 프로세스를 종료한 뒤, 각 서버를 재시작합니다.

## 사용 방법

```powershell
# 두 서버 모두 시작 (기본)
.\start-servers.ps1

# Backend만 시작
.\start-servers.ps1 -BackendOnly

# Frontend만 시작
.\start-servers.ps1 -FrontendOnly

# 서버 확인 없이 바로 시작
.\start-servers.ps1 -SkipCheck
```
