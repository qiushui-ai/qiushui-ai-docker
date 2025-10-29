#!/bin/bash
#
# 秋水AI - 重启脚本
# 用于停止并重新启动所有Docker服务
#

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  秋水AI - 重启服务${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ 错误: 未找到Docker${NC}"
    echo "请先安装Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# 检查Docker是否运行
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ 错误: Docker未运行${NC}"
    echo "请启动Docker Desktop后重试"
    exit 1
fi

# 停止服务
echo -e "${BLUE}🛑 正在停止服务...${NC}"
docker compose down
echo -e "${GREEN}✓ 服务已停止${NC}"
echo ""

# 启动服务
echo -e "${BLUE}🚀 正在启动服务...${NC}"
docker compose up -d

# 等待服务启动
echo ""
echo -e "${BLUE}⏳ 等待服务启动...${NC}"
sleep 10

# 检查服务状态
echo ""
echo -e "${BLUE}📊 服务状态:${NC}"
docker compose ps

# 显示访问信息
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ 服务重启完成!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}访问地址:${NC}"
echo -e "  🌐 Web界面: ${GREEN}http://localhost:9088${NC}"
echo ""
echo -e "${BLUE}其他命令:${NC}"
echo "  查看日志: docker compose logs -f [service_name]"
echo "  停止服务: ./scripts/stop.sh"
echo "  更新服务: ./scripts/update.sh"
echo ""
echo -e "${YELLOW}💡 提示: 首次启动可能需要几分钟来初始化数据库${NC}"
echo ""
