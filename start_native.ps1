# SME v3.0.1 - Native Startup
# Updated: Focused on .venv313 and safe process management

$ErrorActionPreference = "Stop"
$SCRIPT_DIR = $PSScriptRoot
if (-not $SCRIPT_DIR) { $SCRIPT_DIR = Get-Location }
Set-Location $SCRIPT_DIR

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  SME v3.0.1 - Native Startup (No Sidecar)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Determine Python Executable
$PYTHON_EXE = "python"
if (Test-Path ".venv313\Scripts\python.exe") {
    $PYTHON_EXE = "$SCRIPT_DIR\.venv313\Scripts\python.exe"
    Write-Host "Using Virtual Environment: .venv313" -ForegroundColor Gray
} else {
    Write-Host "Warning: .venv313 not found. Falling back to system python." -ForegroundColor Yellow
}

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found. Copy from .env.example" -ForegroundColor Yellow
}

# Function to check port
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

if (Test-PortInUse -Port 8000) { Write-Host "Warning: Port 8000 in use" -ForegroundColor Yellow }
if (Test-PortInUse -Port 5173) { Write-Host "Warning: Port 5173 in use" -ForegroundColor Yellow }

# Create data directory
if (-not (Test-Path "data")) { New-Item -ItemType Directory -Path "data" | Out-Null }

$StartedProcesses = @()

Write-Host "[1/2] Starting SME Operator (port 8000)..." -ForegroundColor Green
$opProc = Start-Process $PYTHON_EXE -ArgumentList "-m src.api.main" -PassThru -NoNewWindow
$StartedProcesses += $opProc

Write-Host "[2/2] Starting Frontend (port 5173)..." -ForegroundColor Green
# npm run dev usually starts vite
$frontProc = Start-Process "npm" -ArgumentList "run dev" -Cwd "$SCRIPT_DIR\frontend" -PassThru -NoNewWindow
$StartedProcesses += $frontProc

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  All services started!" -ForegroundColor Green
Write-Host "  Processes: $($StartedProcesses.Id -join ', ')" -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Operator:   http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend:   http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "  Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan

try {
    while ($true) {
        # Check if processes are still running
        foreach ($proc in $StartedProcesses) {
            if ($proc.HasExited) {
                Write-Host "Process $($proc.Id) has exited unexpectedly!" -ForegroundColor Red
                break
            }
        }
        Start-Sleep -Seconds 2
    }
} finally {
    Write-Host "`nStopping services..." -ForegroundColor Yellow
    foreach ($proc in $StartedProcesses) {
        if (-not $proc.HasExited) {
            Write-Host "Terminating PID $($proc.Id)..." -ForegroundColor Gray
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "Cleanup complete." -ForegroundColor Green
}

