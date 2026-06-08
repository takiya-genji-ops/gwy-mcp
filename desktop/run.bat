@echo off
echo ============================================
echo   gwy-mcp 公考助手
echo ============================================
echo.

REM 检查 .env 文件
if not exist ".env" (
    echo [WARNING] 未找到 .env 文件，请创建并填入 DEEPSEEK_API_KEY
    echo 可以复制 .env.example 并修改:
    echo   copy .env.example .env
    echo   然后编辑 .env 填入你的 API Key
    echo.
)

REM 安装依赖（首次运行）
echo [1/2] 检查依赖...
pip install -e . fastapi uvicorn >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 依赖安装失败，请检查 Python 和网络连接
    pause
    exit /b 1
)

REM 构建前端（如果还没构建）
if not exist "desktop\frontend\dist\index.html" (
    echo 构建前端...
    cd desktop\frontend
    call npm install >nul 2>&1
    call npm run build >nul 2>&1
    cd ..\..
)

REM 启动
echo [2/2] 启动服务...
echo.
echo 服务启动后，在浏览器打开: http://127.0.0.1:8711
echo 按 Ctrl+C 停止服务
echo.
python desktop/backend.py
pause
