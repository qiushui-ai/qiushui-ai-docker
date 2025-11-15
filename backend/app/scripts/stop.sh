#!/bin/bash

# 检查PID文件是否存在
if [ -f "server.pid" ]; then
    PID=$(cat server.pid)
    
    # 检查进程是否仍在运行
    if ps -p $PID > /dev/null; then
        echo "正在停止服务器 (PID: $PID)..."
        kill $PID
        
        # 等待进程结束
        while ps -p $PID > /dev/null; do
            sleep 1
        done
        
        echo "服务器已停止"
    else
        echo "服务器进程已不存在"
    fi
    
    # 删除PID文件
    rm server.pid
    
    # 删除日志文件（可选，取消注释如果你想在停止时删除日志）
    # rm server.log
else
    echo "未找到服务器PID文件，服务器可能未在运行"
fi 