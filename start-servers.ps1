# MOSB Logistics Dashboard - 서버 시작 스크립트
# 서버 시작 전 실행 중인 서버 확인 및 종료 후 재시작

param(
    [switch]$SkipCheck,
    [switch]$BackendOnly,
    [switch]$FrontendOnly
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
    $connections = netstat -ano | Select-String ":$Port\s" | Select-String "LISTENING"
    if ($connections) {
        $pids = $connections | ForEach-Object {
            if ($_ -match "\s+(\d+)$") {
                $matches[1]
            }
        } | Sort-Object -Unique
        return $pids
    }
    return @()
}

function Stop-ServerOnPort {
    param(
        [int]$Port,
        [string]$ServerName
    )
    $pids = Check-Port $Port
    if ($pids.Count -gt 0) {
        Write-ColorOutput Yellow "⚠️  $ServerName (포트 $Port) 실행 중인 프로세스 발견: $($pids -join ', ')"
        foreach ($processId in $pids) {
            try {
                $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
                if ($proc) {
                    Write-ColorOutput Gray "   프로세스 종료 중: $processId ($($proc.ProcessName))"
                    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Milliseconds 500
                }
            } catch {
                Write-ColorOutput Yellow "   경고: 프로세스 $processId 종료 실패 (이미 종료되었을 수 있음)"
            }
        }
        Start-Sleep -Seconds 1
        $remaining = Check-Port $Port
        if ($remaining.Count -eq 0) {
            Write-ColorOutput Green "✅ $ServerName (포트 $Port) 종료 완료"
        } else {
            Write-ColorOutput Red "❌ $ServerName (포트 $Port) 종료 실패. 남은 프로세스: $($remaining -join ', ')"
            return $false
        }
    } else {
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
        $backendJob = Start-Job -ScriptBlock {
            Set-Location $using:BackendDir
            Import-DotEnv (Join-Path $using:BackendDir ".env")
            if (-not $env:DATA_DIR) { $env:DATA_DIR = "./data" }
            if (-not $env:LOGISTICS_DB_PATH) { $env:LOGISTICS_DB_PATH = "./data/logistics.db" }
            if (-not $env:CORS_ORIGINS) { $env:CORS_ORIGINS = "http://localhost:3000" }
            if (-not $env:LOG_LEVEL) { $env:LOG_LEVEL = "INFO" }
            if (-not $env:WS_PING_INTERVAL) { $env:WS_PING_INTERVAL = "10" }
            python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 2>&1
        }

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
            } catch {
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
    } catch {
        Write-ColorOutput Red "❌ Backend 서버 시작 실패: $($_.Exception.Message)"
        return $false
    } finally {
        Pop-Location
    }
}

function Start-Frontend {
    Write-ColorOutput Cyan "`n🚀 Frontend 서버 시작 중..."

    if (-not (Test-Path $FrontendDir)) {
        Write-ColorOutput Red "❌ Frontend 디렉토리를 찾을 수 없습니다: $FrontendDir"
        return $false
    }

    Push-Location $FrontendDir

    Import-DotEnv (Join-Path $FrontendDir ".env.local")
    if (-not $env:NEXT_PUBLIC_API_BASE) {
        $env:NEXT_PUBLIC_API_BASE = "http://localhost:8000"
    }
    if (-not $env:NEXT_PUBLIC_WS_RECONNECT_DELAY) {
        $env:NEXT_PUBLIC_WS_RECONNECT_DELAY = "3000"
    }
    if (-not $env:NEXT_PUBLIC_WS_MAX_RECONNECT_ATTEMPTS) {
        $env:NEXT_PUBLIC_WS_MAX_RECONNECT_ATTEMPTS = "10"
    }
    if (-not $env:NODE_ENV) {
        $env:NODE_ENV = "development"
    }

    try {
        $frontendJob = Start-Job -ScriptBlock {
            Set-Location $using:FrontendDir
            Import-DotEnv (Join-Path $using:FrontendDir ".env.local")
            if (-not $env:NEXT_PUBLIC_API_BASE) { $env:NEXT_PUBLIC_API_BASE = "http://localhost:8000" }
            if (-not $env:NEXT_PUBLIC_WS_RECONNECT_DELAY) { $env:NEXT_PUBLIC_WS_RECONNECT_DELAY = "3000" }
            if (-not $env:NEXT_PUBLIC_WS_MAX_RECONNECT_ATTEMPTS) {
                $env:NEXT_PUBLIC_WS_MAX_RECONNECT_ATTEMPTS = "10"
            }
            if (-not $env:NODE_ENV) { $env:NODE_ENV = "development" }
            npm run dev 2>&1
        }

        Write-ColorOutput Green "✅ Frontend 서버 시작됨 (Job ID: $($frontendJob.Id))"
        Write-ColorOutput Gray "   http://localhost:3000"
        Write-ColorOutput Yellow "   ⏳ 초기 컴파일 중... (30-60초 소요될 수 있음)"

        return $true
    } catch {
        Write-ColorOutput Red "❌ Frontend 서버 시작 실패: $($_.Exception.Message)"
        return $false
    } finally {
        Pop-Location
    }
}

Write-ColorOutput Cyan "═══════════════════════════════════════════════════════"
Write-ColorOutput Cyan "MOSB Logistics Dashboard - 서버 시작 스크립트"
Write-ColorOutput Cyan "═══════════════════════════════════════════════════════`n"

if (-not $SkipCheck) {
    Write-ColorOutput Yellow "1️⃣  실행 중인 서버 확인 중...`n"

    $backendOk = $true
    $frontendOk = $true

    if (-not $FrontendOnly) {
        $backendOk = Stop-ServerOnPort 8000 "Backend"
    }

    if (-not $BackendOnly) {
        $frontendOk = Stop-ServerOnPort 3000 "Frontend"
    }

    if (-not ($backendOk -and $frontendOk)) {
        Write-ColorOutput Red "`n❌ 일부 서버 종료 실패. 수동으로 종료 후 다시 시도하세요."
        exit 1
    }

    Write-ColorOutput Green "`n✅ 모든 서버 확인 완료`n"
    Start-Sleep -Seconds 2
} else {
    Write-ColorOutput Yellow "⏭️  서버 확인 단계 건너뜀 (--SkipCheck 옵션)"
}

Write-ColorOutput Yellow "2️⃣  서버 시작 중...`n"

$backendStarted = $false
$frontendStarted = $false

if (-not $FrontendOnly) {
    $backendStarted = Start-Backend
}

if (-not $BackendOnly) {
    Start-Sleep -Seconds 2
    $frontendStarted = Start-Frontend
}

Write-ColorOutput Cyan "`n═══════════════════════════════════════════════════════"
Write-ColorOutput Cyan "📊 서버 시작 완료"
Write-ColorOutput Cyan "═══════════════════════════════════════════════════════`n"

if ($backendStarted) {
    Write-ColorOutput Green "✅ Backend: http://localhost:8000"
}
if ($frontendStarted) {
    Write-ColorOutput Green "✅ Frontend: http://localhost:3000"
}

Write-ColorOutput Yellow "`n💡 서버 종료: Ctrl+C 또는 작업 관리자에서 프로세스 종료"
Write-Output ""
