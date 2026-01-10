# MOSB Logistics Dashboard - 서버 시작 스크립트
# 서버 시작 전 실행 중인 서버 확인 및 종료 후 재시작

param(
    [switch]$SkipCheck,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$CleanCache
)

$ErrorActionPreference = "Stop"
$script:RootDir = $PSScriptRoot
$BackendDir = Join-Path $script:RootDir "mosb_logistics_dashboard_next_fastapi_mvp\backend"
$FrontendDir = Join-Path $script:RootDir "mosb_logistics_dashboard_next_fastapi_mvp\frontend"

function Write-ColorOutput {
    param(
        [Parameter(Mandatory = $true)][ConsoleColor]$ForegroundColor,
        [Parameter(ValueFromRemainingArguments = $true)][string[]]$Message
    )
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($Message) {
        Write-Output ($Message -join " ")
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Import-DotEnv {
    param(
        [Parameter(Mandatory = $true)][string]$EnvPath
    )
    if (-not (Test-Path $EnvPath)) {
        return
    }
    Get-Content $EnvPath | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            return
        }
        $parts = $line -split "=", 2
        if ($parts.Count -eq 2) {
            $name = $parts[0].Trim()
            $value = $parts[1].Trim().Trim('"')
            if ($name) {
                Set-Item -Path "env:$name" -Value $value
            }
        }
    }
}

function Check-Port {
    param([int]$Port)
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($connections) {
        return ($connections | Select-Object -ExpandProperty OwningProcess -Unique)
    }
    return @()
}

function Fix-NextEnvDts {
    param([string]$FrontendDir)
    $nextEnvPath = Join-Path $FrontendDir "next-env.d.ts"
    if (-not (Test-Path $nextEnvPath)) {
        return $false
    }

    $content = Get-Content $nextEnvPath -Raw -ErrorAction SilentlyContinue
    if (-not $content) {
        return $false
    }

    if ($content -match 'import\s+"\.\/\.next\/dev\/types\/routes\.d\.ts"') {
        Write-ColorOutput Yellow "⚠️  next-env.d.ts에 잘못된 import 발견. 수정 중..."
        # 여러 줄 패턴 처리 (Windows/Unix 줄바꿈 모두 지원)
        $fixedContent = $content -replace '(?m)^\s*import\s+"\.\/\.next\/dev\/types\/routes\.d\.ts"\s*;?\s*\r?\n', ''
        # 빈 줄 정리 (연속된 빈 줄 제거)
        $fixedContent = $fixedContent -replace '(?m)(\r?\n){3,}', "`r`n`r`n"
        Set-Content -Path $nextEnvPath -Value $fixedContent -NoNewline -ErrorAction Stop
        Write-ColorOutput Green "✅ next-env.d.ts 수정 완료"
        return $true
    }
    return $false
}

function Clean-FrontendCache {
    param([string]$FrontendDir)
    $nextDir = Join-Path $FrontendDir ".next"
    if (Test-Path $nextDir) {
        Write-ColorOutput Yellow "🧹 .next 캐시 정리 중..."
        Remove-Item -Recurse -Force $nextDir -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
        if (-not (Test-Path $nextDir)) {
            Write-ColorOutput Green "✅ .next 캐시 정리 완료"
            return $true
        }
        else {
            Write-ColorOutput Red "❌ .next 캐시 정리 실패"
            return $false
        }
    }
    else {
        Write-ColorOutput Gray "   .next 캐시 없음 (건너뜀)"
        return $true
    }
}

function Stop-ServerOnPort {
    param(
        [int]$Port,
        [string]$ServerName
    )

    $pids = Check-Port $Port
    if ($pids.Count -gt 0) {
        Write-ColorOutput Yellow "⚠️  $ServerName (포트 $Port) 실행 중인 프로세스 발견: $($pids -join ', ')"

        # PowerShell Jobs도 확인 (Backend가 Job으로 실행되었을 수 있음)
        $jobs = Get-Job -State Running -ErrorAction SilentlyContinue | Where-Object {
            $_.Location -like "*$Port*" -or $_.Name -like "*$ServerName*"
        }
        if ($jobs) {
            Write-ColorOutput Gray "   관련 PowerShell Jobs 종료 중..."
            foreach ($job in $jobs) {
                Stop-Job -Job $job -ErrorAction SilentlyContinue
                Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
            }
        }

        foreach ($processId in $pids) {
            try {
                $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
                if ($proc) {
                    Write-ColorOutput Gray "   프로세스 종료 중: $processId ($($proc.ProcessName))"
                    # 자식 프로세스도 함께 종료 시도
                    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Milliseconds 500
                }
            }
            catch {
                Write-ColorOutput Yellow "   경고: 프로세스 $processId 종료 실패 (이미 종료되었을 수 있음)"
            }
        }

        # 포트가 해제될 때까지 대기 (최대 5초)
        Start-Sleep -Seconds 1
        $maxWait = 5
        $waited = 0
        $remaining = Check-Port $Port
        while ($remaining.Count -gt 0 -and $waited -lt $maxWait) {
            Start-Sleep -Seconds 1
            $waited++
            $remaining = Check-Port $Port
        }

        if ($remaining.Count -eq 0) {
            Write-ColorOutput Green "✅ $ServerName (포트 $Port) 종료 완료"
        }
        else {
            Write-ColorOutput Red "❌ $ServerName (포트 $Port) 종료 실패. 남은 프로세스: $($remaining -join ', ')"
            Write-ColorOutput Yellow "   💡 수동 종료: Get-Process -Id $($remaining -join ',') | Stop-Process -Force"
            return $false
        }
    }
    else {
        Write-ColorOutput Green "✅ $ServerName (포트 $Port) 실행 중인 프로세스 없음"
    }
    return $true
}

function Start-Backend {
    Write-ColorOutput Cyan "`n🚀 Backend 서버 시작 중..."

    if (-not (Test-Path $BackendDir)) {
        Write-ColorOutput Red "❌ Backend 디렉토리를 찾을 수 없습니다: $BackendDir"
        return $false
    }

    Push-Location $BackendDir

    Import-DotEnv (Join-Path $BackendDir ".env")
    if (-not $env:DATA_DIR) {
        $env:DATA_DIR = "./data"
    }
    if (-not $env:LOGISTICS_DB_PATH) {
        $env:LOGISTICS_DB_PATH = "./data/logistics.db"
    }
    if (-not $env:CORS_ORIGINS) {
        $env:CORS_ORIGINS = "http://localhost:3000"
    }
    if (-not $env:LOG_LEVEL) {
        $env:LOG_LEVEL = "INFO"
    }
    if (-not $env:WS_PING_INTERVAL) {
        $env:WS_PING_INTERVAL = "10"
    }

    try {
        # Job 스코프에서 사용할 환경 변수 준비
        $envVars = @{
            DATA_DIR          = if ($env:DATA_DIR) { $env:DATA_DIR } else { "./data" }
            LOGISTICS_DB_PATH = if ($env:LOGISTICS_DB_PATH) { $env:LOGISTICS_DB_PATH } else { "./data/logistics.db" }
            CORS_ORIGINS      = if ($env:CORS_ORIGINS) { $env:CORS_ORIGINS } else { "http://localhost:3000" }
            LOG_LEVEL         = if ($env:LOG_LEVEL) { $env:LOG_LEVEL } else { "INFO" }
            WS_PING_INTERVAL  = if ($env:WS_PING_INTERVAL) { $env:WS_PING_INTERVAL } else { "10" }
        }

        # .env 파일에서 추가 환경 변수 로드 (Job 스코프 내에서)
        $envFile = Join-Path $BackendDir ".env"
        $envFileContent = if (Test-Path $envFile) { Get-Content $envFile } else { @() }

        $backendJob = Start-Job -ScriptBlock {
            param($BackendDir, $EnvVars, $EnvFileContent)

            Set-Location $BackendDir

            # 환경 변수 설정
            foreach ($key in $EnvVars.Keys) {
                Set-Item -Path "env:$key" -Value $EnvVars[$key] -ErrorAction SilentlyContinue
            }

            # .env 파일 파싱 및 적용
            foreach ($line in $EnvFileContent) {
                $line = $line.Trim()
                if (-not $line -or $line.StartsWith("#")) {
                    continue
                }
                $parts = $line -split "=", 2
                if ($parts.Count -eq 2) {
                    $name = $parts[0].Trim()
                    $value = $parts[1].Trim().Trim('"')
                    if ($name -and -not [string]::IsNullOrWhiteSpace($value)) {
                        Set-Item -Path "env:$name" -Value $value -ErrorAction SilentlyContinue
                    }
                }
            }

            # 기본값 설정
            if (-not $env:DATA_DIR) { $env:DATA_DIR = "./data" }
            if (-not $env:LOGISTICS_DB_PATH) { $env:LOGISTICS_DB_PATH = "./data/logistics.db" }
            if (-not $env:CORS_ORIGINS) { $env:CORS_ORIGINS = "http://localhost:3000" }
            if (-not $env:LOG_LEVEL) { $env:LOG_LEVEL = "INFO" }
            if (-not $env:WS_PING_INTERVAL) { $env:WS_PING_INTERVAL = "10" }

            python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 2>&1
        } -ArgumentList $BackendDir, $envVars, $envFileContent

        # Job ID를 스크립트 스코프 변수에 저장
        $script:BackendJobId = $backendJob.Id

        Write-ColorOutput Green "✅ Backend 서버 시작됨 (Job ID: $($backendJob.Id))"
        Write-ColorOutput Gray "   http://localhost:8000"
        Write-ColorOutput Gray "   http://localhost:8000/docs (API Docs)"

        Start-Sleep -Seconds 3

        $maxAttempts = 10
        $attempt = 0
        $ready = $false
        while ($attempt -lt $maxAttempts -and -not $ready) {
            try {
                Invoke-RestMethod -Uri "http://localhost:8000/docs" -Method GET `
                    -TimeoutSec 2 -ErrorAction Stop | Out-Null
                $ready = $true
                Write-ColorOutput Green "✅ Backend 서버 준비 완료!"
            }
            catch {
                $attempt++
                if ($attempt -lt $maxAttempts) {
                    Start-Sleep -Seconds 1
                }
            }
        }

        if (-not $ready) {
            Write-ColorOutput Yellow "⚠️  Backend 서버 시작 확인 실패 (계속 시도 중일 수 있음)"
        }

        return $true
    }
    catch {
        Write-ColorOutput Red "❌ Backend 서버 시작 실패: $($_.Exception.Message)"
        return $false
    }
    finally {
        Pop-Location
    }
}

function Start-Frontend {
    param([bool]$CleanCache)

    Write-ColorOutput Cyan "`n🚀 Frontend 서버 시작 중..."

    if (-not (Test-Path $FrontendDir)) {
        Write-ColorOutput Red "❌ Frontend 디렉토리를 찾을 수 없습니다: $FrontendDir"
        return $false
    }

    Push-Location $FrontendDir

    # next-env.d.ts 자동 수정
    Fix-NextEnvDts $FrontendDir | Out-Null

    # 캐시 정리 (옵션)
    if ($CleanCache) {
        Clean-FrontendCache $FrontendDir | Out-Null
    }

    # 글로벌 NODE_ENV 제거 (JSX 런타임 오류 방지)
    if ($env:NODE_ENV -eq "production") {
        Write-ColorOutput Yellow "⚠️  글로벌 NODE_ENV=production 감지. 제거 중..."
        Remove-Item Env:\NODE_ENV -ErrorAction SilentlyContinue
    }

    Import-DotEnv (Join-Path $FrontendDir ".env.local")
    if (-not $env:NEXT_PUBLIC_API_BASE) { $env:NEXT_PUBLIC_API_BASE = "http://localhost:8000" }
    if (-not $env:NEXT_PUBLIC_WS_RECONNECT_DELAY) { $env:NEXT_PUBLIC_WS_RECONNECT_DELAY = "3000" }
    if (-not $env:NEXT_PUBLIC_WS_MAX_RECONNECT_ATTEMPTS) { $env:NEXT_PUBLIC_WS_MAX_RECONNECT_ATTEMPTS = "10" }
    $env:NODE_ENV = $null  # 명시적으로 제거

    # cross-env 설치 확인 및 설치
    $packageJsonPath = Join-Path $FrontendDir "package.json"
    $hasCrossEnv = $false
    if (Test-Path $packageJsonPath) {
        $packageJson = Get-Content $packageJsonPath -Raw | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($packageJson -and $packageJson.devDependencies -and $packageJson.devDependencies.'cross-env') {
            $hasCrossEnv = $true
        }
    }

    if (-not $hasCrossEnv) {
        Write-ColorOutput Yellow "⚠️  cross-env가 package.json에 없음. 설치 중..."
        try {
            npm install cross-env@^7.0.3 --save-dev 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput Green "✅ cross-env 설치 완료"
            }
            else {
                Write-ColorOutput Yellow "⚠️  cross-env 설치 중 경고 발생 (계속 진행)"
            }
        }
        catch {
            Write-ColorOutput Yellow "⚠️  cross-env 설치 실패: $($_.Exception.Message) (계속 진행)"
        }
    }
    else {
        # package.json에 있지만 node_modules에 없을 수 있음
        $nodeModulesPath = Join-Path $FrontendDir "node_modules\cross-env"
        if (-not (Test-Path $nodeModulesPath)) {
            Write-ColorOutput Yellow "⚠️  cross-env가 node_modules에 없음. 설치 중..."
            try {
                npm install 2>&1 | Out-Null
                Write-ColorOutput Green "✅ 의존성 설치 완료"
            }
            catch {
                Write-ColorOutput Yellow "⚠️  의존성 설치 중 경고 발생 (계속 진행)"
            }
        }
    }

    try {
        # 새 PowerShell 창에서 실행 (출력 확인 가능)
        $scriptBlock = @"
Set-Location '$FrontendDir'
`$env:NODE_ENV = `$null
if (-not `$env:NEXT_PUBLIC_API_BASE) { `$env:NEXT_PUBLIC_API_BASE = "http://localhost:8000" }
if (-not `$env:NEXT_PUBLIC_WS_RECONNECT_DELAY) { `$env:NEXT_PUBLIC_WS_RECONNECT_DELAY = "3000" }
if (-not `$env:NEXT_PUBLIC_WS_MAX_RECONNECT_ATTEMPTS) { `$env:NEXT_PUBLIC_WS_MAX_RECONNECT_ATTEMPTS = "10" }
npm run dev
"@

        $process = Start-Process powershell -ArgumentList "-NoExit", "-Command", $scriptBlock `
            -WindowStyle Normal -PassThru

        Write-ColorOutput Green "✅ Frontend 서버 시작됨 (PID: $($process.Id), 새 창에서 실행 중)"
        Write-ColorOutput Gray "   http://localhost:3000"
        Write-ColorOutput Yellow "   ⏳ 초기 컴파일 중... (30-60초 소요될 수 있음)"
        Write-ColorOutput Gray "   💡 서버 로그는 새 PowerShell 창에서 확인하세요"

        # 서버 상태 확인 (최대 60초 대기)
        Start-Sleep -Seconds 5
        $maxAttempts = 12
        $attempt = 0
        $ready = $false
        while ($attempt -lt $maxAttempts -and -not $ready) {
            try {
                $conn = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
                if ($conn) {
                    $ready = $true
                    Write-ColorOutput Green "✅ Frontend 서버 포트 3000 리스닝 중"
                }
                else {
                    $attempt++
                    if ($attempt -lt $maxAttempts) {
                        Start-Sleep -Seconds 5
                    }
                }
            }
            catch {
                $attempt++
                if ($attempt -lt $maxAttempts) {
                    Start-Sleep -Seconds 5
                }
            }
        }

        if (-not $ready) {
            Write-ColorOutput Yellow "⚠️  Frontend 서버 포트 확인 실패 (컴파일 중일 수 있음. 새 창 확인 필요)"
        }

        return $true
    }
    catch {
        Write-ColorOutput Red "❌ Frontend 서버 시작 실패: $($_.Exception.Message)"
        return $false
    }
    finally {
        Pop-Location
    }
}

Write-ColorOutput Cyan "═══════════════════════════════════════════════════════"
Write-ColorOutput Cyan "MOSB Logistics Dashboard - 서버 시작 스크립트 (개선 버전)"
Write-ColorOutput Cyan "═══════════════════════════════════════════════════════`n"

if (-not $SkipCheck) {
    Write-ColorOutput Yellow "1️⃣  실행 중인 서버 확인 중...`n"

    # 시작할 서비스 결정
    $shouldStartBackend = -not $FrontendOnly
    $shouldStartFrontend = -not $BackendOnly

    # 양쪽 서비스 포트 확인 (종료하지 않고 확인만)
    # 반대 서비스가 실행 중인지 감지하기 위함
    $backendRunning = (Check-Port 8000).Count -gt 0
    $frontendRunning = (Check-Port 3000).Count -gt 0

    # 시작할 서비스가 아닌 반대 서비스가 실행 중인 경우 정보 메시지
    if ($FrontendOnly -and $backendRunning) {
        Write-ColorOutput Cyan "ℹ️  Backend (포트 8000)가 이미 실행 중입니다. Frontend만 시작합니다."
        Write-ColorOutput Gray "   💡 Backend는 그대로 유지됩니다."
    }
    if ($BackendOnly -and $frontendRunning) {
        Write-ColorOutput Cyan "ℹ️  Frontend (포트 3000)가 이미 실행 중입니다. Backend만 시작합니다."
        Write-ColorOutput Gray "   💡 Frontend는 그대로 유지됩니다."
    }

    # 시작할 서비스의 포트만 종료
    $backendOk = $true
    $frontendOk = $true

    if ($shouldStartBackend) {
        $backendOk = Stop-ServerOnPort 8000 "Backend"
        if (-not $backendOk) {
            Write-ColorOutput Red "`n❌ Backend 서버 종료 실패. 수동으로 종료 후 다시 시도하세요."
            exit 1
        }
    }

    if ($shouldStartFrontend) {
        $frontendOk = Stop-ServerOnPort 3000 "Frontend"
        if (-not $frontendOk) {
            Write-ColorOutput Red "`n❌ Frontend 서버 종료 실패. 수동으로 종료 후 다시 시도하세요."
            exit 1
        }
    }

    Write-ColorOutput Green "`n✅ 모든 서버 확인 완료`n"
    Start-Sleep -Seconds 2
}
else {
    Write-ColorOutput Yellow "⏭️  서버 확인 단계 건너뜀 (--SkipCheck 옵션)"
}

Write-ColorOutput Yellow "2️⃣  서버 시작 중...`n"

$backendStarted = $false
$frontendStarted = $false
$script:BackendJobId = $null

if (-not $FrontendOnly) {
    $result = Start-Backend
    $backendStarted = $result
    # Backend Job ID 저장 (Start-Backend에서 반환하도록 수정 필요하지만, 일단 Get-Job으로 확인 가능)
}

if (-not $BackendOnly) {
    Start-Sleep -Seconds 2
    $frontendStarted = Start-Frontend -CleanCache $CleanCache
}

Write-ColorOutput Cyan "`n═══════════════════════════════════════════════════════"
Write-ColorOutput Cyan "📊 서버 시작 완료"
Write-ColorOutput Cyan "═══════════════════════════════════════════════════════`n"

if ($backendStarted) {
    Write-ColorOutput Green "✅ Backend: http://localhost:8000"
    if ($script:BackendJobId) {
        Write-ColorOutput Gray "   Job ID: $($script:BackendJobId) (확인: Get-Job -Id $($script:BackendJobId))"
    }
    else {
        Write-ColorOutput Gray "   Job 확인: Get-Job"
    }
}
if ($frontendStarted) {
    Write-ColorOutput Green "✅ Frontend: http://localhost:3000"
    Write-ColorOutput Gray "   로그 확인: 새 PowerShell 창"
}

Write-ColorOutput Yellow "`n💡 서버 종료:"
Write-ColorOutput Gray "   - Frontend: 새 PowerShell 창에서 Ctrl+C"
if ($script:BackendJobId) {
    Write-ColorOutput Gray "   - Backend: Stop-Job -Id $($script:BackendJobId); Remove-Job -Id $($script:BackendJobId) -Force"
}
else {
    Write-ColorOutput Gray "   - Backend: `$job = Get-Job | Where-Object { `$_.Command -like '*uvicorn*' }; Stop-Job `$job; Remove-Job `$job -Force"
}
Write-ColorOutput Yellow "`n💡 유용한 명령어:"
Write-ColorOutput Gray "   - 캐시 정리 후 시작: .\start-servers.ps1 -CleanCache"
Write-ColorOutput Gray "   - Frontend만 시작: .\start-servers.ps1 -FrontendOnly"
Write-ColorOutput Gray "   - Backend만 시작: .\start-servers.ps1 -BackendOnly"
Write-ColorOutput Gray "   - 서버 확인 건너뛰기: .\start-servers.ps1 -SkipCheck"
Write-Output ""
