$ErrorActionPreference = "Continue"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimeDir = Join-Path $env:TEMP "black-sea-eco-monitor"
$StateFile = Join-Path $RuntimeDir "processes.json"

Write-Host ""
Write-Host "BLACK SEA ECO MONITOR" -ForegroundColor Green
Write-Host "Stopping launcher-owned processes..." -ForegroundColor DarkGray
Write-Host ""

if (-not (Test-Path $StateFile)) {
    Write-Host "No launcher state file was found." -ForegroundColor Yellow
    Write-Host "Nothing was stopped." -ForegroundColor DarkGray
    exit 0
}

try {
    $state = Get-Content $StateFile -Raw |
        ConvertFrom-Json
}
catch {
    Write-Host "Could not read launcher state file." -ForegroundColor Red
    exit 1
}

function Stop-ProcessTree {
    param(
        [object]$PidValue,
        [bool]$Owned,
        [string]$Name
    )

    if (-not $Owned -or -not $PidValue) {
        Write-Host "${Name}: not launcher-owned; leaving it alone." -ForegroundColor DarkGray
        return
    }

    $pidInt = [int]$PidValue

    $process = Get-Process `
        -Id $pidInt `
        -ErrorAction SilentlyContinue

    if (-not $process) {
        Write-Host "${Name}: already stopped." -ForegroundColor DarkGray
        return
    }

    Write-Host "Stopping $Name (PID $pidInt)..." -ForegroundColor Gray

    & taskkill.exe `
        /PID $pidInt `
        /T `
        /F `
        *> $null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "$Name stopped." -ForegroundColor Green
    }
    else {
        Write-Host "$Name could not be stopped automatically." -ForegroundColor Yellow
    }
}

Stop-ProcessTree `
    -PidValue $state.schedulerPid `
    -Owned ([bool]$state.schedulerOwned) `
    -Name "News scheduler"

Stop-ProcessTree `
    -PidValue $state.frontendPid `
    -Owned ([bool]$state.frontendOwned) `
    -Name "Frontend"

Stop-ProcessTree `
    -PidValue $state.backendPid `
    -Owned ([bool]$state.backendOwned) `
    -Name "FastAPI"

Remove-Item `
    $StateFile `
    -Force `
    -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Done." -ForegroundColor Green
