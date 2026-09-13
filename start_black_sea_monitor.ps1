param(
    [switch]$NoScheduler,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = Join-Path $RepoRoot "backend\venv\Scripts\python.exe"
$FrontendDir = Join-Path $RepoRoot "frontend"

$RuntimeDir = Join-Path $env:TEMP "black-sea-eco-monitor"
$StateFile = Join-Path $RuntimeDir "processes.json"

$BackendOut = Join-Path $RuntimeDir "backend.out.log"
$BackendErr = Join-Path $RuntimeDir "backend.err.log"
$FrontendOut = Join-Path $RuntimeDir "frontend.out.log"
$FrontendErr = Join-Path $RuntimeDir "frontend.err.log"
$SchedulerOut = Join-Path $RuntimeDir "scheduler.out.log"
$SchedulerErr = Join-Path $RuntimeDir "scheduler.err.log"

$BackendUrl = "http://127.0.0.1:8000/"
$FrontendUrl = "http://127.0.0.1:5173/"
$OllamaUrl = "http://127.0.0.1:11434/api/tags"

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

function Write-Step {
    param(
        [string]$Message
    )

    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Test-Http {
    param(
        [string]$Url,
        [int]$TimeoutSec = 2
    )

    try {
        $response = Invoke-WebRequest `
            -Uri $Url `
            -UseBasicParsing `
            -TimeoutSec $TimeoutSec

        return (
            $response.StatusCode -ge 200 `
            -and $response.StatusCode -lt 500
        )
    }
    catch {
        return $false
    }
}

function Wait-ForHttp {
    param(
        [string]$Url,
        [int]$TimeoutSec = 30
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSec)

    while ((Get-Date) -lt $deadline) {
        if (Test-Http -Url $Url -TimeoutSec 2) {
            return $true
        }

        Start-Sleep -Milliseconds 500
    }

    return $false
}

function Show-LogTail {
    param(
        [string]$Path,
        [int]$Lines = 20
    )

    if (Test-Path $Path) {
        Write-Host ""
        Write-Host "Last log lines from $Path" -ForegroundColor Yellow
        Get-Content $Path -Tail $Lines
    }
}

function Start-MonitorProcess {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [string]$StdOut,
        [string]$StdErr
    )

    if (Test-Path $StdOut) {
        Remove-Item $StdOut -Force
    }

    if (Test-Path $StdErr) {
        Remove-Item $StdErr -Force
    }

    return Start-Process `
        -FilePath $FilePath `
        -ArgumentList $Arguments `
        -WorkingDirectory $WorkingDirectory `
        -WindowStyle Hidden `
        -RedirectStandardOutput $StdOut `
        -RedirectStandardError $StdErr `
        -PassThru
}

if (-not (Test-Path $PythonExe)) {
    throw "Python venv not found: $PythonExe"
}

if (-not (Test-Path (Join-Path $FrontendDir "package.json"))) {
    throw "Frontend not found: $FrontendDir"
}

$npmCommand = Get-Command "npm.cmd" -ErrorAction SilentlyContinue

if (-not $npmCommand) {
    throw "npm.cmd was not found in PATH. Install Node.js/npm first."
}

$state = [ordered]@{
    startedAt = (Get-Date).ToString("o")

    backendPid = $null
    backendOwned = $false

    frontendPid = $null
    frontendOwned = $false

    schedulerPid = $null
    schedulerOwned = $false
}

Write-Host ""
Write-Host "BLACK SEA ECO MONITOR" -ForegroundColor Green
Write-Host "Unified local launcher" -ForegroundColor DarkGray

# ------------------------------------------------------------
# Backend
# ------------------------------------------------------------

Write-Step "Checking FastAPI backend"

if (Test-Http -Url $BackendUrl) {
    Write-Host "FastAPI is already running on 127.0.0.1:8000" -ForegroundColor Green
}
else {
    Write-Host "Starting FastAPI..." -ForegroundColor Gray

    $backend = Start-MonitorProcess `
        -FilePath $PythonExe `
        -Arguments @(
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000"
        ) `
        -WorkingDirectory $RepoRoot `
        -StdOut $BackendOut `
        -StdErr $BackendErr

    $state.backendPid = $backend.Id
    $state.backendOwned = $true

    if (-not (Wait-ForHttp -Url $BackendUrl -TimeoutSec 30)) {
        Show-LogTail -Path $BackendErr
        throw "FastAPI did not become ready within 30 seconds."
    }

    Write-Host "FastAPI ready: $BackendUrl" -ForegroundColor Green
}

# ------------------------------------------------------------
# Frontend
# ------------------------------------------------------------

Write-Step "Checking web frontend"

if (Test-Http -Url $FrontendUrl) {
    Write-Host "Frontend is already running on 127.0.0.1:5173" -ForegroundColor Green
}
else {
    Write-Host "Starting Vite frontend..." -ForegroundColor Gray

    $frontend = Start-MonitorProcess `
        -FilePath $npmCommand.Source `
        -Arguments @(
            "run",
            "dev",
            "--",
            "--host",
            "127.0.0.1",
            "--port",
            "5173"
        ) `
        -WorkingDirectory $FrontendDir `
        -StdOut $FrontendOut `
        -StdErr $FrontendErr

    $state.frontendPid = $frontend.Id
    $state.frontendOwned = $true

    if (-not (Wait-ForHttp -Url $FrontendUrl -TimeoutSec 30)) {
        Show-LogTail -Path $FrontendErr
        throw "Frontend did not become ready within 30 seconds."
    }

    Write-Host "Frontend ready: $FrontendUrl" -ForegroundColor Green
}

# ------------------------------------------------------------
# News scheduler
# ------------------------------------------------------------

Write-Step "Checking News Agent scheduler"

if ($NoScheduler) {
    Write-Host "Scheduler disabled by -NoScheduler." -ForegroundColor Yellow
}
elseif (-not (Test-Http -Url $OllamaUrl -TimeoutSec 2)) {
    Write-Host "Ollama is not running. Scheduler will not start." -ForegroundColor Yellow
    Write-Host "The map still works with already stored events." -ForegroundColor DarkGray
}
else {
    Write-Host "Ollama detected. Starting News Agent scheduler..." -ForegroundColor Gray

    $scheduler = Start-MonitorProcess `
        -FilePath $PythonExe `
        -Arguments @(
            "-m",
            "agents.news_agent.scheduler"
        ) `
        -WorkingDirectory $RepoRoot `
        -StdOut $SchedulerOut `
        -StdErr $SchedulerErr

    $state.schedulerPid = $scheduler.Id
    $state.schedulerOwned = $true

    Start-Sleep -Seconds 1

    if ($scheduler.HasExited) {
        Show-LogTail -Path $SchedulerErr
        Write-Host "Scheduler exited early. Backend and frontend remain available." -ForegroundColor Yellow
        $state.schedulerPid = $null
        $state.schedulerOwned = $false
    }
    else {
        Write-Host "Scheduler started (PID $($scheduler.Id))." -ForegroundColor Green
    }
}

# ------------------------------------------------------------
# Save launcher-owned PIDs
# ------------------------------------------------------------

$state |
    ConvertTo-Json |
    Set-Content `
        -Path $StateFile `
        -Encoding UTF8

# ------------------------------------------------------------
# Open browser
# ------------------------------------------------------------

Write-Step "Black Sea Eco Monitor is ready"

Write-Host "Web:       $FrontendUrl" -ForegroundColor Green
Write-Host "API docs:  http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Logs: $RuntimeDir" -ForegroundColor DarkGray
Write-Host "Use STOP_MONITOR.cmd to stop processes launched by this script." -ForegroundColor DarkGray

if (-not $NoBrowser) {
    Start-Process $FrontendUrl
}
