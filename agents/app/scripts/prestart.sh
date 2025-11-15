#!/bin/bash
# 预启动脚本 - 在启动服务器之前执行数据库迁移

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 进入项目根目录
cd "$PROJECT_ROOT"

echo "🔧 执行启动前数据库迁移检查..."

# 确保虚拟环境已安装
if [ ! -d ".venv" ]; then
    echo "📦 初始化虚拟环境..."
    uv sync
fi

# 激活虚拟环境
source .venv/bin/activate

# 执行数据库迁移
echo "🔄 应用所有待处理的数据库迁移..."

# 优先使用项目的 migrate.py 脚本
if [ -f "$PROJECT_ROOT/alembic/migrate.py" ]; then
    echo "   使用 alembic/migrate.py..."
    python3 alembic/migrate.py upgrade
else
    # 如果 migrate.py 不存在，直接使用 Alembic
    echo "   使用 alembic 命令..."
    alembic upgrade head
fi

echo "✅ 数据库迁移完成！"
echo ""

