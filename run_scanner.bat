@echo off
REM GeoJob-Sentinel Runner Script for Windows
REM Automatically activates environment and runs the scanner

echo ====================================
echo GeoJob-Sentinel - Starting Scan
echo ====================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

REM Check if dependencies are installed
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found
    pause
    exit /b 1
)

REM Check if config.yaml exists
if not exist "config.yaml" (
    echo ERROR: config.yaml not found
    echo.
    echo Please copy config.example.yaml to config.yaml and fill in your details:
    echo   copy config.example.yaml config.yaml
    echo   notepad config.yaml
    echo.
    pause
    exit /b 1
)

REM Install/update dependencies
echo Installing dependencies...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Running GeoJob-Sentinel...
echo.

REM Run the application
python geojob_sentinel.py

echo.
echo ====================================
echo Scan Complete
echo ====================================
echo.
echo Check geojob_sentinel.log for details
echo.

pause
