#!/bin/bash
#
# 秋水AI - 停止脚本
# 用于停止所有Docker服务
#

set -e

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  秋水AI - 停止服务${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ 错误: 未找到Docker${NC}"
    exit 1
fi

# 停止服务
echo -e "${BLUE}🛑 正在停止服务...${NC}"
docker compose down

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ 服务已停止${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}💡 提示:${NC}"
echo "  启动服务: ./scripts/start.sh"
echo "  删除所有数据: docker compose down -v"
echo ""
