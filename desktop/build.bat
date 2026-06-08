@echo off
echo ============================================
echo   gwy-mcp Windows 构建脚本
echo ============================================
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] 安装 Python 依赖...
cd /d %~dp0..
pip install -e . fastapi uvicorn pyinstaller 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] 依赖安装失败
    pause
    exit /b 1
)

echo [2/4] 构建前端...
cd /d %~dp0frontend
call npm install 2>nul
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] 前端构建失败
    pause
    exit /b 1
)

echo [3/4] 打包为 exe...
cd /d %~dp0..
pyinstaller --onefile ^
    --name "gwy-mcp" ^
    --add-data "desktop/frontend/dist;frontend/dist" ^
    --add-data "src;src" ^
    --add-data "data;data" ^
    --hidden-import=anthropic ^
    --hidden-import=openai ^
    --hidden-import=pdfplumber ^
    --hidden-import=bs4 ^
    --hidden-import=httpx ^
    --hidden-import=pydantic ^
    --hidden-import=dotenv ^
    --hidden-import=fastapi ^
    --hidden-import=uvicorn ^
    --clean ^
    desktop/backend.py

if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller 打包失败
    pause
    exit /b 1
)

echo.
echo [4/4] 构建完成!
echo.
echo 输出文件: dist\gwy-mcp.exe
echo 使用方法: 双击 gwy-mcp.exe，浏览器打开 http://127.0.0.1:8711
echo.
pause
