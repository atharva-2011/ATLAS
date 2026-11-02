# ==============================================================================
# ATLAS: Developer Environment Setup Script (Windows PowerShell 5.1+)
# ==============================================================================

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = (Resolve-Path "$ScriptDir\..\..").Path

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " ATLAS: Initializing Development Environment in $RootDir" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

Set-Location $RootDir

# 1. Virtual Environment Check / Creation
$VenvPython = "$RootDir\.venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "[1/4] Creating Python 3.12 virtual environment (.venv)..." -ForegroundColor Yellow
    py -3.12 -m venv .venv
} else {
    Write-Host "[1/4] Existing virtual environment found (.venv)." -ForegroundColor Green
}

# 2. Upgrade pip and install baseline tooling
Write-Host "[2/4] Ensuring build and test tooling are installed..." -ForegroundColor Yellow
& $VenvPython -m pip install --upgrade pip setuptools wheel
& $VenvPython -m pip install pytest httpx ruff fastapi "uvicorn[standard]" pydantic-settings

# 3. Install shared packages in editable mode
Write-Host "[3/4] Installing shared packages in editable mode..." -ForegroundColor Yellow
& $VenvPython -m pip install --no-build-isolation -e .\shared\contracts -e .\shared\observability -e .\shared\common -e .\shared\security

# 4. Install all microservices in editable mode
Write-Host "[4/4] Installing all 6 microservices in editable mode..." -ForegroundColor Yellow
& $VenvPython -m pip install --no-build-isolation `
    -e .\services\api_gateway `
    -e .\services\research_orchestrator `
    -e .\services\ingestion_service `
    -e .\services\retrieval_service `
    -e .\services\agent_runtime `
    -e .\services\evaluation_service

Write-Host "`nEnvironment setup successfully completed!" -ForegroundColor Green
Write-Host "Run .\infrastructure\scripts\test_all.ps1 to verify the test suite." -ForegroundColor Cyan
