import os
import sentry_sdk
import logging
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

# 确保在应用启动时加载所有 SQLModel 表模型
import qiushuiai.schemas

from qiushuiai.api.main import api_router
from qiushuiai.core.config import settings
from qiushuiai.core.exceptions import register_exception_handlers

from dotenv import load_dotenv
load_dotenv()

# 添加日志配置（在文件开头，其他代码之前）
# 修改日志配置，确保级别正确设置
logging.basicConfig(
    level=logging.INFO,  # 确保这是 INFO 级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server.log')
    ],
    force=True  # 强制重新配置，防止被其他地方覆盖
)


def custom_generate_unique_id(route: APIRoute) -> str:
    # 如果 route.tags 为空，使用默认的 tag
    if not route.tags:
        return f"default-{route.name}"
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# 注册全局异常处理器
register_exception_handlers(app)

# CORS 中间件
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 包含原有的 API 路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 健康检查端点
@app.get("/api/v1/health")
def health():
    """Health check."""
    return {"status": "ok"}

level = logging.getLogger().level
effective_level = logging.getLogger().getEffectiveLevel()
print(f"当前日志级别: {level} ({logging.getLevelName(level)})")
print(f"根记录器级别: {effective_level} ({logging.getLevelName(effective_level)})")