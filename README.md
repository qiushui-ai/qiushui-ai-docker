# 秋水AI - Docker部署文档

<div align="center">

**一键部署的AI智能助手平台**

支持多种AI模型 | 知识库管理 | 智能对话 | Agent工作流

---

[快速开始](#快速开始) • [系统要求](#系统要求) • [配置说明](#配置说明) • [常见问题](#常见问题) • [技术支持](#技术支持)

</div>

---

## 📋 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [详细配置](#详细配置)
- [服务说明](#服务说明)
- [脚本工具](#脚本工具)
- [常用操作](#常用操作)
- [常见问题](#常见问题)
- [更新日志](#更新日志)
- [技术支持](#技术支持)

---

## 💻 系统要求

### 硬件要求
- **CPU**: 4核心或以上
- **内存**: 8GB RAM或以上 (推荐16GB)
- **硬盘**: 至少20GB可用空间
- **网络**: 稳定的互联网连接

### 软件要求
- **操作系统**:
  - Windows 10/11 (64位)
  - macOS 10.15 或更高版本
  - Linux (Ubuntu 20.04+ / CentOS 8+ / Debian 11+)
- **Docker Desktop**:
  - 版本 20.10.0 或更高
  - [下载Docker Desktop](https://www.docker.com/products/docker-desktop)

---

## 🚀 快速开始

### 步骤1: 安装Docker

#### Windows / macOS
1. 访问 [Docker Desktop官网](https://www.docker.com/products/docker-desktop)
2. 下载并安装Docker Desktop
3. 启动Docker Desktop,等待其完全启动
4. 确认Docker已运行: 打开终端,运行 `docker --version`

#### 🇨🇳 国内用户特别注意
如果您的网络环境无法访问 Docker Hub，请先配置国内镜像源：

**Docker Desktop 配置：**
1. 打开 Docker Desktop
2. 进入 Settings → Docker Engine
3. 添加以下配置并点击 Apply & Restart：
```json
{
  "registry-mirrors": [
    "https://dockerhub.azk8s.cn",
    "https://docker.m.daocloud.io"
  ]
}
```

**OrbStack 配置：**
```bash
mkdir -p ~/.orbstack/config
cat > ~/.orbstack/config/docker.json << 'EOF'
{
  "registry-mirrors": [
    "https://dockerhub.azk8s.cn",
    "https://docker.m.daocloud.io"
  ]
}
EOF
killall OrbStack && open -a OrbStack
```

**Linux 配置：**
```bash
sudo tee /etc/docker/daemon.json > /dev/null << 'EOF'
{
  "registry-mirrors": [
    "https://dockerhub.azk8s.cn",
    "https://docker.m.daocloud.io"
  ]
}
EOF
sudo systemctl daemon-reload
sudo systemctl restart docker
```

📖 更多国内部署说明请参考：[DEPLOY_CN.md](DEPLOY_CN.md)

#### Linux
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker

# CentOS/RHEL
sudo yum install -y docker docker-compose
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户添加到docker组
sudo usermod -aG docker $USER
# 重新登录以使更改生效
```

### 步骤2: 下载并解压项目

将收到的项目压缩包解压到您选择的目录,例如:
- Windows: `C:\qiushui-ai-docker\`
- macOS/Linux: `~/qiushui-ai-docker/`

### 步骤3: 配置环境变量

1. 进入项目目录
2. 复制 `.env.example` 为 `.env`:
   ```bash
   # macOS/Linux
   cp .env.example .env

   # Windows (命令提示符)
   copy .env.example .env
   ```

3. 编辑 `.env` 文件,**必须修改**以下配置:
   ```bash
   # ⚠️ 数据库密码 (必改!)
   POSTGRES_PASSWORD=your_strong_password_here

   # ⚠️ 应用密钥 (必改!)
   SECRET_KEY=your_random_secret_key_here

   # 如果需要使用AI功能,填写对应的API Key
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   ```

   **💡 生成随机密钥的方法:**
   ```bash
   # macOS/Linux
   openssl rand -hex 32

   # 或者使用Python
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

### 步骤4: 启动服务

#### macOS / Linux
```bash
./start.sh
```

#### Windows
双击运行 `start.bat` 或在命令提示符中运行:
```cmd
start.bat
```

### 步骤5: 访问应用

等待几分钟让服务完全启动(首次启动需要初始化数据库),然后在浏览器中访问:

**🌐 http://localhost:9088**

默认管理员账号 (在.env中配置):
- **用户名**: admin@example.com
- **密码**: admin123

---

## ⚙️ 详细配置

### 环境变量说明

打开 `.env` 文件,以下是各配置项的详细说明:

#### 1. 数据库配置 (必填)
```bash
POSTGRES_USER=qiushui                      # 数据库用户名
POSTGRES_PASSWORD=请修改为强密码            # ⚠️ 必须修改!
POSTGRES_DB=qiushui                        # 数据库名称
POSTGRES_PORT=5432                         # 数据库端口
```

#### 2. 应用配置
```bash
PROJECT_NAME=秋水AI                        # 项目名称
ENVIRONMENT=production                     # 运行环境
SECRET_KEY=请修改为随机密钥                 # ⚠️ 必须修改!
BACKEND_CORS_ORIGINS=["http://localhost","http://localhost:9088"]  # 跨域配置
QIUSHUI_AI_BACKEND_HOST=http://backend:16009  # Backend API 地址 (Agents 服务使用)
```

#### 3. AI模型配置 (根据需要)
```bash
# OpenAI (ChatGPT)
OPENAI_API_KEY=sk-...

# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-...

# 智谱AI (向量化模型)
ZHIPUAI_API_KEY=...
```

#### 4. 文件存储配置 (可选)
```bash
# 阿里云OSS
OSS_ACCESS_KEY_ID=...
OSS_ACCESS_KEY_SECRET=...
OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
OSS_BUCKET_NAME=...
```

---

## 🏗️ 服务说明

秋水AI包含以下Docker服务:

| 服务名 | 说明 | 内部端口 | 外部端口 |
|--------|------|----------|----------|
| **nginx** | 前端Web服务 + API网关 | 80 | 9088 |
| **backend** | 主后端API服务 | 16009 | - |
| **agents** | AI Agent工作流服务 | 16001 | - |
| **postgresql** | PostgreSQL数据库 | 5432 | - |

**注意**: 除了nginx(9088端口)外,其他服务不直接暴露到外部,通过nginx进行反向代理。

### API路由规则

- **前端**: `http://localhost:9088/`
- **Backend API**: `http://localhost:9088/api/v1/`
- **Agents API**: `http://localhost:9088/agent/`

---

## 🛠️ 脚本工具

项目提供了一系列便捷的脚本工具，位于 `scripts/` 目录下，用于简化部署和管理操作：

### 核心管理脚本

| 脚本名称 | 平台 | 功能说明 |
|---------|------|----------|
| `start.sh` / `start.bat` | Linux/macOS / Windows | **启动服务** - 检查环境并启动所有Docker服务 |
| `stop.sh` / `stop.bat` | Linux/macOS / Windows | **停止服务** - 停止所有Docker服务 |
| `restart.sh` | Linux/macOS | **重启服务** - 停止后重新启动所有服务 |
| `update.sh` / `update.bat` | Linux/macOS / Windows | **更新服务** - 拉取最新镜像并重启服务 |

### 构建和维护脚本

| 脚本名称 | 平台 | 功能说明 |
|---------|------|----------|
| `rebuild.sh` / `rebuild.bat` | Linux/macOS / Windows | **重新构建** - 清除缓存重新构建所有镜像 |
| `start-rebuild.sh` | Linux/macOS | **强制重建启动** - 重建镜像并启动服务 |

### 环境配置脚本

| 脚本名称 | 平台 | 功能说明 |
|---------|------|----------|
| `check-environment.sh` | Linux/macOS | **环境检查** - 检查部署环境是否满足要求 |
| `setup-cn-mirrors.sh` | Linux/macOS | **配置国内镜像源** - 自动配置Docker国内镜像源 |

### 脚本功能详解

#### 1. 启动相关脚本

**`start.sh` / `start.bat`** - 标准启动流程
- ✅ 检查Docker安装和运行状态
- ✅ 自动创建 `.env` 文件（如果不存在）
- ✅ 创建必要的数据目录
- ✅ 启动所有Docker服务
- ✅ 显示服务状态和访问地址

**`start-rebuild.sh`** - 强制重建启动
- ✅ 执行启动流程的所有检查
- ✅ 强制重新构建所有镜像（清除缓存）
- ✅ 适用于代码更新后的重新部署

#### 2. 更新和维护脚本

**`update.sh` / `update.bat`** - 版本更新
- ✅ 拉取最新的Docker镜像
- ✅ 重启所有服务应用更新
- ✅ 清理过期镜像释放空间

**`rebuild.sh` / `rebuild.bat`** - 完全重构建
- ✅ 停止所有正在运行的服务
- ✅ 清除Docker构建缓存
- ✅ 重新构建所有镜像
- ✅ 启动服务并验证状态

#### 3. 环境配置脚本

**`check-environment.sh`** - 部署前检查
- ✅ 检查Docker安装和运行状态
- ✅ 验证镜像源配置
- ✅ 检查磁盘空间和内存
- ✅ 验证端口占用情况
- ✅ 检查环境变量配置
- ✅ 测试网络连接

**`setup-cn-mirrors.sh`** - 国内镜像源配置
- ✅ 自动检测Docker类型（Docker Desktop/OrbStack/Linux）
- ✅ 配置国内高速镜像源
- ✅ 支持多种操作系统
- ✅ 自动重启Docker服务

### 使用示例

```bash
# 首次部署 - 推荐流程
./scripts/check-environment.sh          # 检查环境
./scripts/setup-cn-mirrors.sh           # 配置镜像源（国内用户）
./scripts/start.sh                       # 启动服务

# 日常操作
./scripts/stop.sh                        # 停止服务
./scripts/restart.sh                     # 重启服务
./scripts/update.sh                      # 更新版本

# 故障排除
./scripts/rebuild.sh                     # 重新构建解决问题
./scripts/start-rebuild.sh               # 强制重建并启动
```

### Windows 用户说明

Windows 用户请使用对应的 `.bat` 脚本：
```cmd
scripts\start.bat          # 启动服务
scripts\stop.bat           # 停止服务
scripts\update.bat         # 更新服务
scripts\rebuild.bat        # 重新构建
```

---

## 📝 常用操作

### 查看服务状态
```bash
docker compose ps
```

### 查看日志
```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f agents
docker compose logs -f nginx
```

### 停止服务
```bash
# macOS/Linux
./stop.sh

# Windows
stop.bat
```

### 重启服务
```bash
# macOS/Linux
./stop.sh && ./start.sh

# Windows
stop.bat 然后 start.bat
```

### 更新服务
```bash
# macOS/Linux
./update.sh

# Windows
update.bat
```

### 备份数据

**数据库备份:**
```bash
docker exec qiushui-postgresql pg_dump -U qiushui qiushuiai > backup_qiushui_$(date +%Y%m%d).sql
docker exec qiushui-postgresql pg_dump -U qiushui qiushuiai_conversation > backup_conversation_$(date +%Y%m%d).sql
```

**数据卷备份:**
```bash
# 备份整个volumes目录
tar -czf qiushui_volumes_backup_$(date +%Y%m%d).tar.gz volumes/
```

### 恢复数据

**恢复数据库:**
```bash
cat backup_qiushui_20240101.sql | docker exec -i qiushui-postgresql psql -U qiushui qiushuiai
```

### 清理和重置

**⚠️ 警告: 以下操作会删除所有数据!**

```bash
# 停止并删除所有容器和数据卷
docker compose down -v

# 删除所有镜像
docker rmi $(docker images 'qiushui/*' -q)

# 清理所有数据
rm -rf volumes/postgres_data/*
rm -rf volumes/logs/*
```

---

## ❓ 常见问题

### 1. 端口9088被占用怎么办?

**问题**: 启动时提示 "Bind for 0.0.0.0:9088 failed: port is already allocated"

**解决方法1** - 修改端口:
编辑 `docker-compose.yml`,找到nginx服务的ports配置:
```yaml
nginx:
  ports:
    - "9088:80"  # 改为其他端口,如 "8080:80"
```

**解决方法2** - 关闭占用端口的程序:
```bash
# macOS/Linux - 查找占用9088端口的进程
lsof -i :9088

# Windows - 查找占用9088端口的进程
netstat -ano | findstr :9088

# 然后终止对应的进程
```

### 2. Docker启动失败

**问题**: 运行start.sh/start.bat时提示Docker相关错误

**可能原因和解决方法**:
1. **Docker Desktop未启动**:
   - 确保Docker Desktop正在运行
   - Windows: 检查系统托盘
   - macOS: 检查顶部菜单栏

2. **Docker服务未运行** (Linux):
   ```bash
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

3. **权限问题** (Linux):
   ```bash
   sudo usermod -aG docker $USER
   # 然后重新登录
   ```

### 3. 服务启动很慢或卡住

**可能原因**:
1. **首次启动初始化数据库** - 等待3-5分钟
2. **网络较慢** - Docker拉取镜像需要时间
3. **硬件资源不足** - 检查CPU和内存使用率

**查看启动进度**:
```bash
docker compose logs -f
```

### 4. 无法访问http://localhost:9088

**检查步骤**:

1. **确认服务已启动**:
   ```bash
   docker compose ps
   # 所有服务都应该是 "Up" 状态
   ```

2. **检查nginx日志**:
   ```bash
   docker compose logs nginx
   ```

3. **测试端口连通性**:
   ```bash
   # macOS/Linux
   curl http://localhost:9088/nginx-health

   # Windows (PowerShell)
   Invoke-WebRequest http://localhost:9088/nginx-health
   ```

4. **检查防火墙设置** - 确保9088端口未被防火墙拦截

### 5. 数据库连接失败

**问题**: 服务日志中出现数据库连接错误

**解决方法**:

1. **检查PostgreSQL服务**:
   ```bash
   docker compose ps postgresql
   docker compose logs postgresql
   ```

2. **验证数据库配置** - 确保`.env`文件中的数据库配置正确

3. **重置数据库**:
   ```bash
   docker compose down
   docker volume rm qiushui-ai-docker_postgres_data
   docker compose up -d
   ```

### 6. AI功能不可用

**可能原因**:
1. **未配置API Key** - 检查`.env`文件中的`OPENAI_API_KEY`等配置
2. **API Key无效** - 验证API Key是否正确且有效
3. **网络问题** - 确保能访问相应的AI服务API

**测试API连通性**:
```bash
# 测试OpenAI API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 7. 如何查看详细错误信息?

```bash
# 查看所有服务的实时日志
docker compose logs -f

# 查看特定服务的完整日志
docker compose logs backend --tail=100

# 进入容器内部检查
docker exec -it qiushui-backend /bin/bash
```

---

## 🔄 更新日志

### v1.0.0 (2024-01-01)
- ✨ 首次发布
- 🐳 完整的Docker容器化方案
- 🔒 Python代码Cython编译保护
- 📦 一键部署脚本
- 📝 完善的用户文档

---

## 💬 技术支持

如果您遇到问题或需要帮助:

1. **查看文档**: 首先查看本文档的[常见问题](#常见问题)部分
2. **查看日志**: 使用 `docker compose logs` 查看详细错误信息
3. **联系支持**:
   - 📧 公众号: **我叫秋水**
   - 🌐 官网: [待补充]
   - 💬 社区论坛: [待补充]

---

## 📄 许可证

[待补充许可证信息]

---

## 🙏 致谢

感谢您使用秋水AI!如果觉得不错,请分享给更多朋友。

---

<div align="center">

**秋水AI** - 让AI更简单

Made with ❤️ by 秋水团队

</div>
