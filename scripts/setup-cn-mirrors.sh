#!/bin/bash
#
# 秋水AI - 国内镜像源配置脚本
# 
# 使用方法: ./setup-cn-mirrors.sh
#

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  $1${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# 检测操作系统和 Docker 类型
detect_environment() {
    print_step "检测环境"
    
    OS="$(uname -s)"
    
    # 检测 Docker 类型
    if command -v docker &> /dev/null; then
        DOCKER_TYPE=$(docker version 2>/dev/null | grep -o "OrbStack\|Docker Desktop" | head -1 || echo "unknown")
        
        if [[ "$OS" == "Darwin" ]]; then
            if [[ "$DOCKER_TYPE" == "OrbStack" ]]; then
                DOCKER_TYPE="OrbStack"
            else
                DOCKER_TYPE="Docker Desktop"
            fi
        fi
    else
        print_error "未检测到 Docker，请先安装 Docker"
        exit 1
    fi
    
    print_info "操作系统: $OS"
    print_info "Docker 类型: $DOCKER_TYPE"
}

# 配置 OrbStack
configure_orbstack() {
    print_step "配置 OrbStack 镜像源"
    
    CONFIG_DIR="$HOME/.orbstack/config"
    CONFIG_FILE="$CONFIG_DIR/docker.json"
    
    mkdir -p "$CONFIG_DIR"
    
    cat > "$CONFIG_FILE" << 'EOF'
{
  "registry-mirrors": [
    "https://dockerhub.azk8s.cn",
    "https://docker.m.daocloud.io",
    "https://mirror.baidubce.com"
  ]
}
EOF
    
    print_success "配置文件已创建: $CONFIG_FILE"
    print_info "请手动重启 OrbStack"
    print_info "运行命令: killall OrbStack && open -a OrbStack"
}

# 配置 Docker Desktop
configure_docker_desktop() {
    print_step "配置 Docker Desktop 镜像源"
    
    echo "请按照以下步骤手动配置："
    echo ""
    echo "1. 打开 Docker Desktop"
    echo "2. 进入 Settings (或 Preferences) → Docker Engine"
    echo "3. 在 JSON 配置框中添加以下内容："
    echo ""
    echo "{"
    echo "  \"registry-mirrors\": ["
    echo "    \"https://dockerhub.azk8s.cn\","
    echo "    \"https://docker.m.daocloud.io\","
    echo "    \"https://mirror.baidubce.com\""
    echo "  ]"
    echo "}"
    echo ""
    echo "4. 点击 \"Apply & Restart\""
    echo ""
}

# 配置 Linux Docker
configure_linux() {
    print_step "配置 Linux Docker 镜像源"
    
    DAEMON_CONFIG="/etc/docker/daemon.json"
    
    if [ -f "$DAEMON_CONFIG" ]; then
        print_info "备份现有配置: $DAEMON_CONFIG.backup"
        sudo cp "$DAEMON_CONFIG" "$DAEMON_CONFIG.backup"
    fi
    
    sudo tee "$DAEMON_CONFIG" > /dev/null << 'EOF'
{
  "registry-mirrors": [
    "https://dockerhub.azk8s.cn",
    "https://docker.m.daocloud.io",
    "https://mirror.baidubce.com"
  ]
}
EOF
    
    print_success "配置已写入: $DAEMON_CONFIG"
    print_info "重启 Docker 服务..."
    
    sudo systemctl daemon-reload
    sudo systemctl restart docker
    
    print_success "Docker 已重启"
}

# 验证配置
verify_config() {
    print_step "验证配置"
    
    sleep 2
    
    if docker info | grep -q "dockerhub.azk8s.cn"; then
        print_success "镜像源配置成功！"
        docker info | grep -A 5 "Registry Mirrors:"
    else
        print_error "镜像源配置可能未生效"
        print_info "请检查配置并重启 Docker"
        docker info | grep -A 5 "Registry" || echo "无法获取 Registry 信息"
    fi
}

# 测试镜像拉取
test_pull() {
    print_step "测试镜像拉取"
    
    if docker pull hello-world:latest 2>&1 | grep -q "up to date\|Downloaded"; then
        print_success "镜像拉取测试成功！"
        docker rmi hello-world:latest 2>/dev/null || true
    else
        print_error "镜像拉取测试失败"
        print_info "可能的原因："
        print_info "1. 网络连接问题"
        print_info "2. 镜像源配置未生效（请重启 Docker）"
        print_info "3. 镜像源暂时不可用"
    fi
}

# 主函数
main() {
    print_info "秋水AI - 国内镜像源配置工具"
    
    detect_environment
    
    case "$OS" in
        Darwin)
            if [ "$DOCKER_TYPE" == "OrbStack" ]; then
                configure_orbstack
            else
                configure_docker_desktop
            fi
            ;;
        Linux)
            configure_linux
            ;;
        *)
            print_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac
    
    echo ""
    read -p "是否重启 Docker 以应用配置？(y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ "$OS" == "Darwin" && "$DOCKER_TYPE" == "OrbStack" ]]; then
            killall OrbStack 2>/dev/null && sleep 2 && open -a OrbStack || print_info "无法自动重启，请手动重启 OrbStack"
        elif [[ "$OS" == "Linux" ]]; then
            sudo systemctl restart docker
        fi
    fi
    
    if [[ "$OS" == "Linux" || "$DOCKER_TYPE" == "OrbStack" ]]; then
        verify_config
    fi
    
    read -p "是否测试镜像拉取？(y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_pull
    fi
    
    echo ""
    print_success "配置完成！"
    print_info "如果遇到问题，请查看 DEPLOY_CN.md 了解更多信息"
}

# 运行
main

