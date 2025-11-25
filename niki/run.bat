@echo off
REM Deadlock Detection & Recovery Toolkit - Windows Runner
REM This script sets up and runs the web dashboard automatically

echo ========================================
echo  Deadlock Detection Toolkit
echo  AI-Powered System Monitor
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Checking Python installation...
python --version

REM Check if virtual environment exists
if not exist "venv\" (
    echo.
    echo [2/4] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
) else (
    echo.
    echo [2/4] Virtual environment already exists
)

REM Activate virtual environment and install requirements
echo.
echo [3/4] Installing dependencies...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install or upgrade requirements
pip install --upgrade pip >nul 2>&1
pip install fastapi uvicorn[standard] websockets networkx pydantic click pyyaml pytest pytest-asyncio -q
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully!

REM Run the web dashboard
echo.
echo [4/4] Starting web dashboard...
echo.
echo ========================================
echo  Dashboard URL: http://localhost:8000
echo  Press Ctrl+C to stop the server
echo ========================================
echo.

python -m visualizer.app

REM If the server stops, wait for user
pause
