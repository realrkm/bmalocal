<#
.SYNOPSIS
    BMALocal Unified Local Service Launcher
.DESCRIPTION
    Launches MySQL verification, Anvil App Server, and Walkie Talkie chat daemon.
    Supports -forTests flag to isolate the test database schema.
.PARAMETER forTests
    Switch parameter to point the application to the test database for E2E tests.
#>

param (
    [switch]$forTests
)

$ErrorActionPreference = "Stop"
$appRoot = "d:\BMAAutoAccessories\venv\Lib\site-packages\BMALocal"
Set-Location $appRoot

Write-Host "==================================================" -ForegroundColor Cyan
if ($forTests) {
    Write-Host " Starting BMALocal in TEST MODE (Isolated Test DB)" -ForegroundColor Yellow
    $env:DB_NAME = "bma_test_db"
} else {
    Write-Host " Starting BMALocal in DEVELOPMENT MODE" -ForegroundColor Cyan
}
Write-Host "=================================================="

# 1. Run Pre-flight Checks
Write-Host "[1/3] Running pre-flight environment checks..." -ForegroundColor Gray
$checkScript = Join-Path $appRoot ".agents\skills\bmalocal-service-runner\scripts\check-prereqs.ps1"
if (Test-Path $checkScript) {
    & powershell -ExecutionPolicy Bypass -File $checkScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Pre-flight checks failed. Aborting startup." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

# 2. Ensure log directory exists
$logDir = Join-Path $appRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

# 3. Start Anvil App Server
Write-Host "[2/3] Starting Anvil App Server on port 8080..." -ForegroundColor Cyan
Write-Host "      Logs redirected to logs\service_output.log" -ForegroundColor Gray

# If LAN certificates exist, start with HTTPS; otherwise HTTP mode
$certFile = Join-Path $appRoot "cert\192.168.100.12.pem"
$keyFile  = Join-Path $appRoot "cert\192.168.100.12-key.pem"

if ((Test-Path $certFile) -and (Test-Path $keyFile)) {
    Write-Host "[3/3] SSL Certificates detected. Launching in HTTPS mode..." -ForegroundColor Green
    & anvil-app-server --app . --origin https://192.168.100.12:443 --manual-cert-file $certFile --manual-cert-key-file $keyFile --auto-migrate
} else {
    Write-Host "[3/3] Launching in local HTTP mode (http://localhost:8080)..." -ForegroundColor Green
    & anvil-app-server --app . --port 8080 --auto-migrate
}
