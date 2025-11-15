#!/bin/bash
# 重启脚本 - 停止服务器，然后启动服务器

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔄 正在重启服务器..."

# 停止服务器
"$SCRIPT_DIR/stop.sh"

# 等待一秒确保进程完全停止
sleep 1

# 启动服务器
exec "$SCRIPT_DIR/start.sh"
