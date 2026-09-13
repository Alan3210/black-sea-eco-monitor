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
$RunId = Get-Date -Format "yyyyMMdd-HHmmss"

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

function Test-ProcessRunning {
    param(
        [object]$PidValue
    )

    if (-not $PidValue) {
        return $false
    }

    $process = Get-Process `
        -Id ([int]$PidValue) `
        -ErrorAction SilentlyContinue

    return $null -ne $process
}

function Find-ProcessByCommandLine {
    param(
        [string]$Pattern
    )

    try {
        $match = Get-CimInstance Win32_Process |
            Where-Object {
                $_.CommandLine `
                -and $_.CommandLine -match $Pattern
            } |
            Select-Object -First 1

        if ($match) {
            return [int]$match.ProcessId
        }
    }
    catch {
        # Best-effort only. Failure here must not prevent startup.
    }

    return $null
}

function Read-ExistingState {
    if (-not (Test-Path $StateFile)) {
        return $null
    }

    try {
        return Get-Content $StateFile -Raw |
            ConvertFrom-Json
    }
    catch {
        Write-Host "Ignoring unreadable old launcher state." -ForegroundColor Yellow
        return $null
    }
}

function Save-State {
    param(
        [hashtable]$State
    )

    $State |
        ConvertTo-Json |
        Set-Content `
            -Path $StateFile `
            -Encoding UTF8
}

function Show-LogTail {
    param(
        [string]$Path,
        [int]$Lines = 20
    )

    if ($Path -and (Test-Path $Path)) {
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
        [string]$Name
    )

    # Each new process gets NEW log files. This is deliberate:
    # a running process keeps its redirect file open on Windows, so trying
    # to delete/reuse that file causes "file is being used by another process".
    $SafeName = $Name.ToLower().Replace(" ", "-")
    $StdOut = Join-Path $RuntimeDir "$SafeName-$RunId.out.log"
    $StdErr = Join-Path $RuntimeDir "$SafeName-$RunId.err.log"

    $process = Start-Process `
        -FilePath $FilePath `
        -ArgumentList $Arguments `
        -WorkingDirectory $WorkingDirectory `
        -WindowStyle Hidden `
        -RedirectStandardOutput $StdOut `
        -RedirectStandardError $StdErr `
        -PassThru

    return @{
        Process = $process
        StdOut = $StdOut
        StdErr = $StdErr
    }
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

$oldState = Read-ExistingState

$state = @{
    startedAt = (Get-Date).ToString("o")

    backendPid = $null
    backendOwned = $false
    backendStdOut = $null
    backendStdErr = $null

    frontendPid = $null
    frontendOwned = $false
    frontendStdOut = $null
    frontendStdErr = $null

    schedulerPid = $null
    schedulerOwned = $false
    schedulerStdOut = $null
    schedulerStdErr = $null
}

# Preserve ownership from a previous successful launcher run.
# This makes START_MONITOR.cmd safe to run twice: STOP_MONITOR.cmd will still
# know which already-running processes belong to us.
if ($oldState) {
    if (
        $oldState.backendOwned `
        -and (Test-ProcessRunning $oldState.backendPid)
    ) {
        $state.backendPid = [int]$oldState.backendPid
        $state.backendOwned = $true
        $state.backendStdOut = $oldState.backendStdOut
        $state.backendStdErr = $oldState.backendStdErr
    }

    if (
        $oldState.frontendOwned `
        -and (Test-ProcessRunning $oldState.frontendPid)
    ) {
        $state.frontendPid = [int]$oldState.frontendPid
        $state.frontendOwned = $true
        $state.frontendStdOut = $oldState.frontendStdOut
        $state.frontendStdErr = $oldState.frontendStdErr
    }

    if (
        $oldState.schedulerOwned `
        -and (Test-ProcessRunning $oldState.schedulerPid)
    ) {
        $state.schedulerPid = [int]$oldState.schedulerPid
        $state.schedulerOwned = $true
        $state.schedulerStdOut = $oldState.schedulerStdOut
        $state.schedulerStdErr = $oldState.schedulerStdErr
    }
}

Save-State $state

Write-Host ""
Write-Host "BLACK SEA ECO MONITOR" -ForegroundColor Green
Write-Host "Unified local launcher v2" -ForegroundColor DarkGray

# ------------------------------------------------------------
# Backend
# ------------------------------------------------------------

Write-Step "Checking FastAPI backend"

if (Test-Http -Url $BackendUrl) {
    if ($state.backendOwned) {
        Write-Host "FastAPI is already running (launcher-owned, PID $($state.backendPid))." -ForegroundColor Green
    }
    else {
        Write-Host "FastAPI is already running on 127.0.0.1:8000 (external/manual)." -ForegroundColor Green
    }
}
else {
    Write-Host "Starting FastAPI..." -ForegroundColor Gray

    $started = Start-MonitorProcess `
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
        -Name "backend"

    $state.backendPid = $started.Process.Id
    $state.backendOwned = $true
    $state.backendStdOut = $started.StdOut
    $state.backendStdErr = $started.StdErr
    Save-State $state

    if (-not (Wait-ForHttp -Url $BackendUrl -TimeoutSec 30)) {
        Show-LogTail -Path $state.backendStdErr
        throw "FastAPI did not become ready within 30 seconds."
    }

    Write-Host "FastAPI ready: $BackendUrl" -ForegroundColor Green
}

# ------------------------------------------------------------
# Frontend
# ------------------------------------------------------------

Write-Step "Checking web frontend"

if (Test-Http -Url $FrontendUrl) {
    if ($state.frontendOwned) {
        Write-Host "Frontend is already running (launcher-owned, PID $($state.frontendPid))." -ForegroundColor Green
    }
    else {
        Write-Host "Frontend is already running on 127.0.0.1:5173 (external/manual)." -ForegroundColor Green
    }
}
else {
    Write-Host "Starting Vite frontend..." -ForegroundColor Gray

    $started = Start-MonitorProcess `
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
        -Name "frontend"

    $state.frontendPid = $started.Process.Id
    $state.frontendOwned = $true
    $state.frontendStdOut = $started.StdOut
    $state.frontendStdErr = $started.StdErr
    Save-State $state

    if (-not (Wait-ForHttp -Url $FrontendUrl -TimeoutSec 30)) {
        Show-LogTail -Path $state.frontendStdErr
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
elseif (
    $state.schedulerOwned `
    -and (Test-ProcessRunning $state.schedulerPid)
) {
    Write-Host "Scheduler is already running (launcher-owned, PID $($state.schedulerPid))." -ForegroundColor Green
}
else {
    # If the state file was lost, still avoid creating a duplicate scheduler.
    $manualSchedulerPid = Find-ProcessByCommandLine `
        "agents\.news_agent\.scheduler"

    if ($manualSchedulerPid) {
        Write-Host "Scheduler is already running (external/manual, PID $manualSchedulerPid)." -ForegroundColor Green
        $state.schedulerPid = $null
        $state.schedulerOwned = $false
        Save-State $state
    }
    else {
        Write-Host "Ollama detected. Starting News Agent scheduler..." -ForegroundColor Gray

        $started = Start-MonitorProcess `
            -FilePath $PythonExe `
            -Arguments @(
                "-m",
                "agents.news_agent.scheduler"
            ) `
            -WorkingDirectory $RepoRoot `
            -Name "scheduler"

        $state.schedulerPid = $started.Process.Id
        $state.schedulerOwned = $true
        $state.schedulerStdOut = $started.StdOut
        $state.schedulerStdErr = $started.StdErr
        Save-State $state

        Start-Sleep -Seconds 1

        if ($started.Process.HasExited) {
            Show-LogTail -Path $state.schedulerStdErr

            Write-Host "Scheduler exited early. Backend and frontend remain available." -ForegroundColor Yellow

            $state.schedulerPid = $null
            $state.schedulerOwned = $false
            Save-State $state
        }
        else {
            Write-Host "Scheduler started (PID $($started.Process.Id))." -ForegroundColor Green
        }
    }
}

# ------------------------------------------------------------
# Finish
# ------------------------------------------------------------

$state.startedAt = (Get-Date).ToString("o")
Save-State $state

Write-Step "Black Sea Eco Monitor is ready"

Write-Host "Web:       $FrontendUrl" -ForegroundColor Green
Write-Host "API docs:  http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Logs: $RuntimeDir" -ForegroundColor DarkGray
Write-Host "START_MONITOR.cmd can now be run repeatedly without starting duplicate services." -ForegroundColor DarkGray
Write-Host "Use STOP_MONITOR.cmd to stop launcher-owned processes." -ForegroundColor DarkGray

if (-not $NoBrowser) {
    Start-Process $FrontendUrl
}
