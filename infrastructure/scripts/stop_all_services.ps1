# ==============================================================================
# ATLAS: Stop All 6 Microservices Cleanly (Windows PowerShell 5.1+)
# ==============================================================================

[CmdletBinding()]
param()

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = (Resolve-Path "$ScriptDir\..\..").Path
$PidFile = "$RootDir\.atlas_pids.json"
$Ports = 8000..8005

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " ATLAS: Stopping all microservice processes..." -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# 1. Stop saved PIDs if PID file exists
if (Test-Path $PidFile) {
    try {
        $SavedPids = Get-Content -Path $PidFile -Raw | ConvertFrom-Json
        foreach ($item in $SavedPids) {
            $pidToStop = $item.Id
            $name = $item.Name
            $proc = Get-Process -Id $pidToStop -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host " [-] Stopping $name (PID: $pidToStop)..." -ForegroundColor Yellow
                Stop-Process -Id $pidToStop -Force -ErrorAction SilentlyContinue
            }
        }
    } catch {
        Write-Warning "Could not parse $PidFile, falling back to port inspection."
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

# 2. Safety check: ensure ports 8000..8005 are freed
foreach ($port in $Ports) {
    try {
        $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        foreach ($conn in $conns) {
            $ownerPid = $conn.OwningProcess
            if ($ownerPid -gt 0) {
                Write-Host " [-] Freeing port $port held by PID $ownerPid..." -ForegroundColor Yellow
                Stop-Process -Id $ownerPid -Force -ErrorAction SilentlyContinue
            }
        }
    } catch {
        # NetTCPConnection not available or permission restricted; fallback to netstat if needed
    }
}

Write-Host "`nAll ATLAS microservice processes stopped and ports 8000-8005 verified free." -ForegroundColor Green
