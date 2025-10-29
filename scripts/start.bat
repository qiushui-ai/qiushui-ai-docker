@echo off
REM 秋水AI - 启动脚本 (Windows)
REM 用于启动所有Docker服务

chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ========================================
echo   秋水AI - 启动服务
echo ========================================
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Docker
    echo 请先安装Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM 检查Docker是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: Docker未运行
    echo 请启动Docker Desktop后重试
    pause
    exit /b 1
)

REM 检查.env文件
if not exist ".env" (
    echo ⚠️  警告: 未找到.env文件
    if exist ".env.example" (
        echo 正在从.env.example创建.env文件...
        copy ".env.example" ".env" >nul
        echo ✓ .env文件已创建
        echo 请编辑.env文件,设置必要的配置(特别是POSTGRES_PASSWORD)
        echo.
        pause
    ) else (
        echo ❌ 错误: 未找到.env.example文件
        pause
        exit /b 1
    )
)

REM 创建必要的目录
echo 📁 检查数据目录...
if not exist "volumes\postgres_data" mkdir volumes\postgres_data
if not exist "volumes\logs\backend" mkdir volumes\logs\backend
if not exist "volumes\logs\agents" mkdir volumes\logs\agents
if not exist "volumes\logs\postgres" mkdir volumes\logs\postgres

REM 启动服务
echo 🚀 正在启动服务...
echo.
docker compose up -d

REM 等待服务启动
echo.
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo.
echo 📊 服务状态:
docker compose ps

REM 显示访问信息
echo.
echo ========================================
echo   ✓ 服务启动完成!
echo ========================================
echo.
echo 访问地址:
echo   🌐 Web界面: http://localhost:9088
echo.
echo 其他命令:
echo   查看日志: docker compose logs -f [service_name]
echo   停止服务: stop.bat
echo   重启服务: stop.bat 然后 start.bat
echo   更新服务: update.bat
echo.
echo 💡 提示: 首次启动可能需要几分钟来初始化数据库
echo.
pause
