# PowerShell script to run the Deadlock Detection Toolkit
# This script sets up and runs the web dashboard automatically

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Deadlock Detection Toolkit" -ForegroundColor Cyan
Write-Host " AI-Powered System Monitor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "[1/4] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host $pythonVersion -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.9+ from https://www.python.org/" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if virtual environment exists
Write-Host ""
if (-not (Test-Path "venv")) {
    Write-Host "[2/4] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "Virtual environment created successfully!" -ForegroundColor Green
} else {
    Write-Host "[2/4] Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment and install requirements
Write-Host ""
Write-Host "[3/4] Installing dependencies..." -ForegroundColor Yellow

& "$PSScriptRoot\venv\Scripts\Activate.ps1"

# Install or upgrade requirements
pip install --upgrade pip *>$null
pip install fastapi uvicorn[standard] websockets networkx pydantic click pyyaml pytest pytest-asyncio -q

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "Dependencies installed successfully!" -ForegroundColor Green

# Run the web dashboard
Write-Host ""
Write-Host "[4/4] Starting web dashboard..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Dashboard URL: http://localhost:8000" -ForegroundColor Green
Write-Host " Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

python -m visualizer.app

# If the server stops, wait for user
Read-Host "Press Enter to exit"
