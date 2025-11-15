#!/bin/bash
# 停止脚本 - 停止正在运行的服务器

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# PID文件路径
PID_FILE="$PROJECT_ROOT/logs/server.pid"

# 尝试通过PID文件停止
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "🛑 正在停止服务器 (PID: $PID)..."
        kill "$PID" 2>/dev/null || true
        
        # 等待进程结束（最多等待5秒）
        for i in {1..10}; do
            if ! ps -p "$PID" > /dev/null 2>&1; then
                break
            fi
            sleep 0.5
        done
        
        # 如果进程仍在运行，强制杀死
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "⚠️  进程未正常结束，强制停止..."
            kill -9 "$PID" 2>/dev/null || true
        fi
        
        echo "✅ 服务器已停止"
        rm -f "$PID_FILE"
        exit 0
    else
        # PID文件存在但进程不存在，清理PID文件
        rm -f "$PID_FILE"
    fi
fi

# 如果PID文件不存在或无效，尝试通过进程名查找并停止
RUN_SERVER_PIDS=$(pgrep -f "run_server.py" || true)
if [ -n "$RUN_SERVER_PIDS" ]; then
    echo "🛑 发现运行中的服务器进程，正在停止..."
    for PID in $RUN_SERVER_PIDS; do
        echo "   停止进程 (PID: $PID)..."
        kill "$PID" 2>/dev/null || true
    done
    
    # 等待进程结束
    sleep 1
    
    # 强制停止仍在运行的进程
    for PID in $(pgrep -f "run_server.py" 2>/dev/null || true); do
        echo "⚠️  强制停止进程 (PID: $PID)..."
        kill -9 "$PID" 2>/dev/null || true
    done
    
    echo "✅ 服务器已停止"
else
    echo "ℹ️  未发现运行中的服务器进程"
fi

