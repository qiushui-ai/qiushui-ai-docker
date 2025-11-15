#!/bin/bash
# 启动脚本 - 启动后直接输出日志到终端

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 进入项目根目录
cd "$PROJECT_ROOT"

# PID文件路径
PID_FILE="$PROJECT_ROOT/logs/server.pid"

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "⚠️  服务器已经在运行中 (PID: $PID)"
        echo "   使用 'scripts/stop.sh' 来停止服务器"
        exit 1
    else
        # PID文件存在但进程不存在，删除旧PID文件
        rm -f "$PID_FILE"
    fi
fi

# 确保虚拟环境已安装
if [ ! -d ".venv" ]; then
    echo "📦 初始化虚拟环境..."
    uv sync
fi

# 激活虚拟环境
source .venv/bin/activate

# 执行启动前数据库迁移
if [ -f "$SCRIPT_DIR/prestart.sh" ]; then
    "$SCRIPT_DIR/prestart.sh"
else
    echo "⚠️  未找到 prestart.sh 脚本，跳过数据库迁移"
fi

# 启动服务器（前台运行，直接输出日志到终端）
echo "🚀 启动服务器..."
echo "📍 服务器将运行在: http://localhost:${PORT:-8000}"
echo "📊 API文档将运行在: http://localhost:${PORT:-8000}/docs"
echo "💡 按 Ctrl+C 停止服务器"
echo ""

# 设置信号处理，确保退出时清理PID文件
cleanup() {
    if [ -f "$PID_FILE" ]; then
        SERVER_PID=$(cat "$PID_FILE")
        kill "$SERVER_PID" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
    exit 0
}
trap cleanup SIGINT SIGTERM

# 后台启动服务器，输出仍显示在终端
python3 run_server.py &
SERVER_PID=$!

# 保存服务器进程的PID
echo $SERVER_PID > "$PID_FILE"

# 等待服务器进程结束（这样日志会直接输出到终端）
wait $SERVER_PID

# 清理PID文件
rm -f "$PID_FILE"

