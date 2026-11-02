# ==============================================================================
# ATLAS: Run All Lint and Test Checks (Windows PowerShell 5.1+)
# ==============================================================================

[CmdletBinding()]
param()

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = (Resolve-Path "$ScriptDir\..\..").Path
$VenvPython = "$RootDir\.venv\Scripts\python.exe"

Set-Location $RootDir

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " ATLAS: Running Monorepo Quality Gates & Test Suites " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# 1. Ruff lint
Write-Host "`n[1/3] Running Ruff linting..." -ForegroundColor Yellow
& $RootDir\.venv\Scripts\ruff.exe check .
if ($LASTEXITCODE -ne 0) {
    Write-Error "Ruff linting failed."
    exit 1
}

# 2. Ruff formatting check
Write-Host "`n[2/3] Checking code formatting..." -ForegroundColor Yellow
& $RootDir\.venv\Scripts\ruff.exe format --check .
if ($LASTEXITCODE -ne 0) {
    Write-Error "Ruff format check failed."
    exit 1
}

# 3. Pytest
Write-Host "`n[3/3] Running full test suite (pytest)..." -ForegroundColor Yellow
& $RootDir\.venv\Scripts\pytest.exe -v
if ($LASTEXITCODE -ne 0) {
    Write-Error "Pytest suite failed."
    exit 1
}

Write-Host "`n=====================================================" -ForegroundColor Green
Write-Host " ALL CHECKS PASSED: 100% Quality Gates Satisfied! " -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
