@echo off
REM 秋水AI - 重新构建脚本 (Windows)
REM 清除缓存并重新构建所有Docker镜像

echo ========================================
echo   秋水AI - 重新构建镜像
echo ========================================
echo.

REM 检查Docker是否安装
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到Docker
    exit /b 1
)

REM 停止所有服务
echo [停止] 停止现有服务...
docker compose down

REM 清除缓存并重新构建
echo.
echo [构建] 重新构建镜像 (清除缓存)...
echo 这可能需要几分钟时间...
echo.

docker compose build

echo.
echo [完成] 镜像构建完成

REM 启动服务
echo.
echo [启动] 启动服务...
docker compose up -d

REM 等待服务启动
echo.
echo [等待] 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo.
echo [状态] 服务状态:
docker compose ps

REM 清理悬挂镜像
echo.
echo [清理] 清理旧镜像...
docker image prune -f

echo.
echo ========================================
echo   完成! 重建完成
echo ========================================
echo.
echo 访问地址:
echo   Web界面: http://localhost:9088
echo.

pause
