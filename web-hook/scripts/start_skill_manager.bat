@echo off
REM Skill Manager 启动脚本

echo ========================================
echo   Skill Manager Server
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python first.
    pause
    exit /b 1
)

REM 进入脚本目录
cd /d "%~dp0"

REM 检查虚拟环境
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
echo Installing dependencies...
pip install -r requirements.txt -q

REM 启动服务器
echo.
echo Starting server...
echo.
python skill_server.py

pause