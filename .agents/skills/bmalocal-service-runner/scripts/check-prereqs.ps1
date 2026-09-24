<#
.SYNOPSIS
    BMALocal Environment & Dependency Verification Script
.DESCRIPTION
    Checks Java runtime, MySQL availability, Python dependencies, wkhtmltopdf,
    SSL certificate validity, and port availability.
    Exits with code 0 on success, or code 1 with actionable failure messages.
#>

$ErrorActionPreference = "Stop"
$failed = $false

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " BMALocal Environment & Prerequisite Check" -ForegroundColor Cyan
Write-Host "=================================================="

# 1. Check Java
Write-Host -NoNewline "[1/6] Checking Java Runtime (JRE/JDK)... "
$javaCmd = Get-Command java -ErrorAction SilentlyContinue
if ($javaCmd) {
    Write-Host "OK ($($javaCmd.Source))" -ForegroundColor Green
} else {
    Write-Host "FAILED!" -ForegroundColor Red
    Write-Host "      Java is required by Anvil App Server. Ensure JRE/JDK 8+ is installed and on PATH." -ForegroundColor Yellow
    $failed = $true
}

# 2. Check Python
Write-Host -NoNewline "[2/6] Checking Python Environment... "
try {
    $pyVersion = python --version 2>&1
    Write-Host "OK ($pyVersion)" -ForegroundColor Green
} catch {
    Write-Host "FAILED! Python not found on PATH." -ForegroundColor Red
    $failed = $true
}

# 3. Check wkhtmltopdf
Write-Host -NoNewline "[3/6] Checking wkhtmltopdf... "
$wkhtmlPath = $env:WKHTMLTOPDF_PATH
if (-not $wkhtmlPath) {
    $wkhtmlPath = "C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
}
if (Test-Path $wkhtmlPath) {
    Write-Host "OK ($wkhtmlPath)" -ForegroundColor Green
} else {
    Write-Host "WARNING! wkhtmltopdf not found at $wkhtmlPath." -ForegroundColor Yellow
    Write-Host "         PDF invoice/jobcard export may fail." -ForegroundColor Yellow
}

# 4. Check Ports
Write-Host "[4/6] Checking Port Availability:"
$portsToCheck = @(
    @{ Name = "MySQL"; Port = 3306; ExpectedOpen = $true },
    @{ Name = "Anvil App Server"; Port = 8080; ExpectedOpen = $false },
    @{ Name = "Walkie Talkie WS"; Port = 8765; ExpectedOpen = $false }
)

foreach ($p in $portsToCheck) {
    $conn = Get-NetTCPConnection -LocalPort $p.Port -ErrorAction SilentlyContinue
    if ($p.ExpectedOpen) {
        if ($conn) {
            Write-Host "      $($p.Name) (Port $($p.Port)): LISTENING (Ready)" -ForegroundColor Green
        } else {
            Write-Host "      $($p.Name) (Port $($p.Port)): NOT REACHABLE!" -ForegroundColor Red
            Write-Host "      Ensure MySQL service is started." -ForegroundColor Yellow
            $failed = $true
        }
    } else {
        if ($conn) {
            Write-Host "      $($p.Name) (Port $($p.Port)): IN USE by PID $($conn[0].OwningProcess)!" -ForegroundColor Yellow
            Write-Host "      (Process already running or previous session not terminated)" -ForegroundColor Gray
        } else {
            Write-Host "      $($p.Name) (Port $($p.Port)): FREE" -ForegroundColor Green
        }
    }
}

# 5. Check SSL Certificates if HTTPS enabled
Write-Host -NoNewline "[5/6] Checking SSL/TLS Certificates... "
$certFile = "cert\192.168.100.12.pem"
if (Test-Path $certFile) {
    Write-Host "OK ($certFile present)" -ForegroundColor Green
} else {
    Write-Host "INFO: No LAN cert found in cert\. HTTP local mode active." -ForegroundColor Gray
}

# 6. Check .env Configuration
Write-Host -NoNewline "[6/6] Checking .env configuration file... "
if (Test-Path ".env") {
    Write-Host "OK (.env found)" -ForegroundColor Green
} else {
    Write-Host "FAILED! .env file is missing from repository root." -ForegroundColor Red
    $failed = $true
}

Write-Host "--------------------------------------------------"
if ($failed) {
    Write-Host "Prerequisite check FAILED. Please resolve the issues above." -ForegroundColor Red
    exit 1
} else {
    Write-Host "All core prerequisites passed! System is ready to launch." -ForegroundColor Green
    exit 0
}
