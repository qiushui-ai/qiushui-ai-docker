#!/bin/bash
#
# 秋水AI - 更新脚本
# 用于更新Docker镜像并重启服务
#

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  秋水AI - 更新服务${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ 错误: 未找到Docker${NC}"
    exit 1
fi

# 拉取最新镜像
echo -e "${BLUE}📥 正在拉取最新镜像...${NC}"
docker compose pull

echo ""
echo -e "${GREEN}✓ 镜像更新完成${NC}"

# 重启服务
echo ""
echo -e "${BLUE}🔄 正在重启服务...${NC}"
docker compose up -d

# 等待服务启动
echo ""
echo -e "${BLUE}⏳ 等待服务启动...${NC}"
sleep 10

# 检查服务状态
echo ""
echo -e "${BLUE}📊 服务状态:${NC}"
docker compose ps

# 清理旧镜像
echo ""
echo -e "${BLUE}🧹 清理旧镜像...${NC}"
docker image prune -f

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ 更新完成!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}访问地址:${NC}"
echo -e "  🌐 Web界面: ${GREEN}http://localhost:9088${NC}"
echo ""
