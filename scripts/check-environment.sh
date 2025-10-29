#!/bin/bash
#
# 秋水AI - 环境检查脚本
# 检查部署环境是否满足要求
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

checks_passed=0
checks_failed=0

check_docker() {
    print_section "检查 Docker"
    
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        print_success "Docker 已安装: $DOCKER_VERSION"
        ((checks_passed++))
        
        if docker ps &> /dev/null; then
            print_success "Docker 正在运行"
            ((checks_passed++))
        else
            print_error "Docker 未运行，请启动 Docker"
            ((checks_failed++))
            return
        fi
        
        # 检查镜像源配置
        REGISTRIES=$(docker info 2>/dev/null | grep -A 5 "Registry Mirrors:" | grep -E "https?://" || echo "")
        if [ -n "$REGISTRIES" ]; then
            print_info "已配置镜像源："
            echo "$REGISTRIES" | sed 's/^/  /'
            ((checks_passed++))
        else
            print_warning "未检测到镜像源配置"
            print_info "国内用户建议运行: ./setup-cn-mirrors.sh"
            ((checks_failed++))
        fi
    else
        print_error "Docker 未安装"
        ((checks_failed++))
    fi
}

check_disk_space() {
    print_section "检查磁盘空间"
    
    AVAILABLE=$(df -h . | tail -1 | awk '{print $4}')
    print_info "可用空间: $AVAILABLE"
    
    # 检查是否有至少 10GB 空间
    AVAILABLE_BYTES=$(df . | tail -1 | awk '{print $4}')
    if [ "$AVAILABLE_BYTES" -gt 10485760 ]; then
        print_success "磁盘空间充足"
        ((checks_passed++))
    else
        print_warning "可用磁盘空间可能不足（推荐至少 20GB）"
        ((checks_failed++))
    fi
}

check_memory() {
    print_section "检查内存"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        TOTAL_MEM=$(sysctl -n hw.memsize)
        TOTAL_MEM_GB=$((TOTAL_MEM / 1073741824))
    else
        # Linux
        TOTAL_MEM=$(free -b | awk '/^Mem:/{print $2}')
        TOTAL_MEM_GB=$((TOTAL_MEM / 1073741824))
    fi
    
    print_info "总内存: ${TOTAL_MEM_GB}GB"
    
    if [ "$TOTAL_MEM_GB" -ge 8 ]; then
        print_success "内存充足（推荐 >= 8GB）"
        ((checks_passed++))
    else
        print_warning "内存可能不足（推荐至少 8GB）"
        ((checks_failed++))
    fi
}

check_ports() {
    print_section "检查端口占用"
    
    local ports=(9088 5432 16009 16002 16001)
    local all_free=true
    
    for port in "${ports[@]}"; do
        if lsof -i :$port &>/dev/null || nc -z localhost $port 2>/dev/null; then
            local proc=$(lsof -i :$port 2>/dev/null | tail -1 | awk '{print $2}' || echo "unknown")
            print_warning "端口 $port 已被占用（进程: $proc）"
            all_free=false
            ((checks_failed++))
        else
            print_success "端口 $port 可用"
            ((checks_passed++))
        fi
    done
}

check_env_file() {
    print_section "检查环境变量文件"
    
    if [ -f ".env" ]; then
        print_success "找到 .env 文件"
        ((checks_passed++))
        
        if grep -q "POSTGRES_PASSWORD" .env && ! grep -q "POSTGRES_PASSWORD=change_me" .env; then
            print_success ".env 文件已配置"
            ((checks_passed++))
        else
            print_warning ".env 文件需要配置 POSTGRES_PASSWORD"
            ((checks_failed++))
        fi
    else
        print_warning "未找到 .env 文件"
        print_info "可以运行: cp .env.example .env"
        ((checks_failed++))
    fi
}

check_network_connectivity() {
    print_section "检查网络连接"
    
    if curl -s -m 5 https://www.baidu.com &>/dev/null; then
        print_success "网络连接正常"
        ((checks_passed++))
    else
        print_warning "网络连接异常"
        ((checks_failed++))
    fi
    
    # 测试 Docker Hub 镜像源
    if docker info 2>/dev/null | grep -q "registry-1.docker.io"; then
        print_warning "检测到直接连接 Docker Hub，国内用户可能较慢"
    fi
}

show_summary() {
    print_section "检查总结"
    
    echo "通过的检查: $checks_passed"
    echo "失败的检查: $checks_failed"
    echo ""
    
    if [ $checks_failed -eq 0 ]; then
        print_success "所有检查通过！可以开始部署。"
        echo ""
        echo "下一步："
        echo "  1. 确保 .env 文件已正确配置"
        echo "  2. 运行: ./build.sh"
        echo "  3. 运行: ./start.sh"
    else
        print_warning "有 $checks_failed 个检查未通过"
        echo ""
        echo "建议："
        if [ $checks_failed -gt 0 ]; then
            echo "  - 查看上述错误信息"
            echo "  - 参考 DEPLOY_CN.md 获取帮助"
            echo "  - 配置 Docker 镜像源: ./setup-cn-mirrors.sh"
        fi
    fi
}

# 运行所有检查
main() {
    echo -e "${GREEN}秋水AI - 环境检查${NC}"
    echo ""
    
    check_docker
    check_disk_space
    check_memory
    check_ports
    check_env_file
    check_network_connectivity
    
    show_summary
}

main

