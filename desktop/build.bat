@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   gwy-mcp Windows Build Script
echo ============================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.10+:
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Installing Python dependencies...
cd /d "%~dp0.."
python -m pip install -e . fastapi uvicorn pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo [2/4] Building frontend...
cd /d "%~dp0frontend"
call npm install >nul 2>&1
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed.
    pause
    exit /b 1
)

echo [3/4] Packaging with PyInstaller...
cd /d "%~dp0.."
python -m PyInstaller --onefile ^
    --name "gwy-mcp" ^
    --add-data "desktop/frontend/dist;frontend/dist" ^
    --add-data "src;src" ^
    --add-data "data;data" ^
    --hidden-import=openai ^
    --hidden-import=httpx ^
    --hidden-import=pydantic ^
    --hidden-import=dotenv ^
    --hidden-import=fastapi ^
    --hidden-import=uvicorn ^
    --hidden-import=bs4 ^
    --hidden-import=pdfplumber ^
    --clean ^
    desktop/backend.py

if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller packaging failed.
    pause
    exit /b 1
)

echo.
echo [4/4] Build complete!
echo Output: dist\gwy-mcp.exe
echo Run it and open http://127.0.0.1:8711
echo.
pause
