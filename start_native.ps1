# SME Native Startup Script (Windows PowerShell)
# Run the full stack natively (no Docker, no sidecar)

$ErrorActionPreference = "Stop"

$SCRIPT_DIR = $PSScriptRoot
if (-not $SCRIPT_DIR) { $SCRIPT_DIR = Get-Location }
Set-Location $SCRIPT_DIR

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  SME v3.0.1 - Native Startup (No Sidecar)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found. Copy from .env.example" -ForegroundColor Yellow
}

# Check if ports are in use
function Test-PortInUse {
    param([int]$Port)
    $connection = New-Object System.Net.Sockets.TcpClient
    try {
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $true
    } catch {
        return $false
    }
}

if (Test-PortInUse -Port 8000) { Write-Host "Warning: Port 8000 in use - Operator may already be running" -ForegroundColor Yellow }
if (Test-PortInUse -Port 5173) { Write-Host "Warning: Port 5173 in use - Frontend may already be running" -ForegroundColor Yellow }

# Create data directory if it doesn't exist
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
}

Write-Host "[1/2] Starting SME Operator (port 8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m src.api.main" -WindowStyle Normal
$operatorPid = $PID

Write-Host "[2/2] Starting Frontend (port 5173)..." -ForegroundColor Green
Set-Location "frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev" -WindowStyle Normal
Set-Location $SCRIPT_DIR

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  All services started!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Operator:   http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend:   http://localhost:5173" -ForegroundColor White
Write-Host "  API Docs:   http://localhost:8000/api/docs" -ForegroundColor White
Write-Host ""
Write-Host "  Note: AI provider runs inside operator (no separate sidecar)" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan

# Wait for user interrupt
try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    Write-Host "Stopping services..." -ForegroundColor Yellow
    Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}
