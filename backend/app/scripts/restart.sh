#!/bin/bash

echo "正在重启服务器..."

# 停止服务器
echo "正在停止服务器..."
./scripts/stop.sh

# 等待一会儿确保服务完全停止
sleep 2

# 启动服务器
echo "正在启动服务器..."
./scripts/start.sh
