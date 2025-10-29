# =============================================================================
# Backend服务 - 运行阶段
# =============================================================================
FROM python:3.12-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=16009

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 安装uv包管理器
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 复制依赖文件（uv.lock 必须存在）
COPY app/pyproject.toml app/uv.lock ./

# 使用 uv sync 安装依赖（不包含项目本身）
# 使用 --frozen 标志确保必须使用 uv.lock，如果不存在或过期则报错
RUN uv sync --no-dev --no-install-project --frozen

# 将虚拟环境添加到 PATH，使容器能找到可执行文件
ENV PATH="/app/.venv/bin:$PATH"

# 复制编译后的代码（.so 文件和必要的 .py 文件）
COPY app/ /app/

# 创建日志目录
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 16009

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import httpx; httpx.get('http://localhost:16009/health', timeout=5.0)" || exit 1

# 启动命令
CMD ["uvicorn", "qiushuiai.main:app", "--host", "0.0.0.0", "--port", "16009"]
