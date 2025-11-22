#!/bin/bash
#
# 秋水AI - 重新构建脚本
# 清除缓存并重新构建所有Docker镜像
#

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  秋水AI - 重新构建镜像${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ 错误: 未找到Docker${NC}"
    exit 1
fi

# 停止所有服务
echo -e "${BLUE}🛑 停止现有服务...${NC}"
docker compose down

# 清除缓存并重新构建
echo ""
echo -e "${BLUE}🔨 重新构建镜像 (清除缓存)...${NC}"
echo -e "${YELLOW}这可能需要几分钟时间...${NC}"
echo ""

docker compose build

echo ""
echo -e "${GREEN}✓ 镜像构建完成${NC}"

# 启动服务
echo ""
echo -e "${BLUE}🚀 启动服务...${NC}"
docker compose up -d

# 等待服务启动
echo ""
echo -e "${BLUE}⏳ 等待服务启动...${NC}"
sleep 10

# 检查服务状态
echo ""
echo -e "${BLUE}📊 服务状态:${NC}"
docker compose ps

# 清理悬挂镜像
echo ""
echo -e "${BLUE}🧹 清理旧镜像...${NC}"
docker image prune -f

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ 重建完成!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}访问地址:${NC}"
echo -e "  🌐 Web界面: ${GREEN}http://localhost:9088${NC}"
echo ""
