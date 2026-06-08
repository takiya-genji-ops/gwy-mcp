@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   gwy-mcp Launcher
echo ============================================
echo.

if not exist "..\.env" (
    echo [WARN] No .env file found. Create one with your DEEPSEEK_API_KEY.
    echo Copy .env.example and edit it: copy .env.example .env
    echo.
)

echo [1/2] Checking dependencies...
cd /d "%~dp0.."
pip install -e . fastapi uvicorn >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies.
    echo Make sure Python 3.10+ is installed: https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist "desktop\frontend\dist\index.html" (
    echo Building frontend...
    cd desktop\frontend
    call npm install >nul 2>&1
    call npm run build >nul 2>&1
    cd ..\..
)

echo [2/2] Starting server...
echo.
echo Open in browser: http://127.0.0.1:8711
echo Press Ctrl+C to stop.
echo.
python desktop\backend.py
pause
