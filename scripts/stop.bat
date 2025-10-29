@echo off
REM 秋水AI - 停止脚本 (Windows)
REM 用于停止所有Docker服务

chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ========================================
echo   秋水AI - 停止服务
echo ========================================
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Docker
    pause
    exit /b 1
)

REM 停止服务
echo 🛑 正在停止服务...
docker compose down

echo.
echo ========================================
echo   ✓ 服务已停止
echo ========================================
echo.
echo 💡 提示:
echo   启动服务: start.bat
echo   删除所有数据: docker compose down -v
echo.
pause
