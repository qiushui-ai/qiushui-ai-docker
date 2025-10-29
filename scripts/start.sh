#!/bin/bash
#
# 秋水AI - 启动脚本
# 用于启动所有Docker服务
#

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  秋水AI - 启动服务${NC}"
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

# 检查.env文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  警告: 未找到.env文件${NC}"
    if [ -f ".env.example" ]; then
        echo -e "${BLUE}正在从.env.example创建.env文件...${NC}"
        cp .env.example .env
        echo -e "${GREEN}✓ .env文件已创建${NC}"
        echo -e "${YELLOW}请编辑.env文件,设置必要的配置(特别是POSTGRES_PASSWORD)${NC}"
        echo ""
        read -p "按Enter继续,或Ctrl+C退出编辑.env文件..."
    else
        echo -e "${RED}❌ 错误: 未找到.env.example文件${NC}"
        exit 1
    fi
fi

# 创建必要的目录
echo -e "${BLUE}📁 检查数据目录...${NC}"
mkdir -p volumes/postgres_data volumes/logs/{backend,agents,postgres}

# 启动服务
echo -e "${GREEN}🚀 正在启动服务...${NC}"
echo ""

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
echo -e "${GREEN}  ✓ 服务启动完成!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}访问地址:${NC}"
echo -e "  🌐 Web界面: ${GREEN}http://localhost:9088${NC}"
echo ""
echo -e "${BLUE}其他命令:${NC}"
echo "  查看日志: docker compose logs -f [service_name]"
echo "  停止服务: ./scripts/stop.sh"
echo "  重启服务: ./scripts/restart.sh"
echo "  更新服务: ./scripts/update.sh"
echo ""
echo -e "${YELLOW}💡 提示: 首次启动可能需要几分钟来初始化数据库${NC}"
echo ""
