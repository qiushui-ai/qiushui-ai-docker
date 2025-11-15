#!/bin/bash

# 杀掉占用9999端口的进程
echo "正在检查并杀掉占用16009端口的进程..."
lsof -ti:16009 | xargs kill -9 2>/dev/null || true
sleep 1

uv sync --python 3.12
# 激活虚拟环境
source .venv/bin/activate

# 运行预启动脚本（自动创建数据库和表，运行迁移，初始化数据）
echo "正在初始化数据库..."
bash scripts/prestart.sh || {
    echo "⚠️ 数据库初始化失败，但继续启动服务器..."
}

# 启动服务器并将进程ID保存到文件中
echo "正在启动服务器..."
nohup uvicorn qiushuiai.main:app --host 0.0.0.0 --port 16009 --reload > server.log 2>&1 &
echo $! > server.pid

echo "服务器已启动在端口 16009"
echo "可以通过以下地址访问："
echo "API文档: http://localhost:16009/docs"
echo "API接口: http://localhost:16009/api/v1"
echo "服务器日志保存在 server.log 文件中" 

# 直接输出服务器日志，方便实时查看
tail -f server.log
