# ==============================================================================
# ATLAS: Start All 6 Microservices Simultaneously (Windows PowerShell 5.1+)
# ==============================================================================

[CmdletBinding()]
param(
    [switch]$NewWindow
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = (Resolve-Path "$ScriptDir\..\..").Path
$VenvPython = "$RootDir\.venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtual environment python not found at $VenvPython. Run .\infrastructure\scripts\setup_dev.ps1 first."
}

Set-Location $RootDir

$Services = @(
    @{ Name = "API Gateway"; Package = "api_gateway.main:app"; Port = 8000 },
    @{ Name = "Research Orchestrator"; Package = "research_orchestrator.main:app"; Port = 8001 },
    @{ Name = "Ingestion Service"; Package = "ingestion_service.main:app"; Port = 8002 },
    @{ Name = "Retrieval Service"; Package = "retrieval_service.main:app"; Port = 8003 },
    @{ Name = "Agent Runtime"; Package = "agent_runtime.main:app"; Port = 8004 },
    @{ Name = "Evaluation Service"; Package = "evaluation_service.main:app"; Port = 8005 }
)

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " ATLAS: Starting All 6 Microservices locally" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

$PidList = @()

foreach ($svc in $Services) {
    $Name = $svc.Name
    $Package = $svc.Package
    $Port = $svc.Port
    $Args = "-m uvicorn $Package --host 127.0.0.1 --port $Port"

    if ($NewWindow) {
        $proc = Start-Process -FilePath $VenvPython -ArgumentList $Args -PassThru
    } else {
        $proc = Start-Process -FilePath $VenvPython -ArgumentList $Args -WindowStyle Hidden -PassThru
    }

    $PidList += @{ Name = $Name; Port = $Port; Id = $proc.Id }
    Write-Host " [+] Started $Name (PID: $($proc.Id)) on http://127.0.0.1:$Port" -ForegroundColor Green
}

# Persist PIDs for graceful teardown
$PidFile = "$RootDir\.atlas_pids.json"
$PidList | ConvertTo-Json | Set-Content -Path $PidFile -Encoding UTF8

Write-Host "`nAll 6 services launched. PID list saved to .atlas_pids.json" -ForegroundColor Green
Write-Host "To stop all services, run: .\infrastructure\scripts\stop_all_services.ps1" -ForegroundColor Yellow
