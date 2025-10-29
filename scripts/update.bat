@echo off
REM 秋水AI - 更新脚本 (Windows)
REM 用于更新Docker镜像并重启服务

chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ========================================
echo   秋水AI - 更新服务
echo ========================================
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Docker
    pause
    exit /b 1
)

REM 拉取最新镜像
echo 📥 正在拉取最新镜像...
docker compose pull

echo.
echo ✓ 镜像更新完成

REM 重启服务
echo.
echo 🔄 正在重启服务...
docker compose up -d

REM 等待服务启动
echo.
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo.
echo 📊 服务状态:
docker compose ps

REM 清理旧镜像
echo.
echo 🧹 清理旧镜像...
docker image prune -f

echo.
echo ========================================
echo   ✓ 更新完成!
echo ========================================
echo.
echo 访问地址:
echo   🌐 Web界面: http://localhost:9088
echo.
pause
