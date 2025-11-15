"""配置管理模块 - 从环境变量读取配置"""
import os
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self):
        self.server = os.getenv("POSTGRES_SERVER", "localhost")
        self.user = os.getenv("POSTGRES_USER", "postgres")
        self.password = os.getenv("POSTGRES_PASSWORD", "")
        self.database = os.getenv("POSTGRES_DB", "qiushuiai")
        self.port = os.getenv("POSTGRES_PORT", "5432")
    
    @property
    def url(self) -> str:
        """生成 asyncpg 格式的数据库 URL"""
        if self.password:
            return f"postgresql+asyncpg://{self.user}:{self.password}@{self.server}:{self.port}/{self.database}"
        else:
            return f"postgresql+asyncpg://{self.user}@{self.server}:{self.port}/{self.database}"
    
    @property
    def url_sync(self) -> str:
        """生成同步格式的数据库 URL（用于 Alembic）"""
        if self.password:
            return f"postgresql+asyncpg://{self.user}:{self.password}@{self.server}:{self.port}/{self.database}"
        else:
            return f"postgresql+asyncpg://{self.user}@{self.server}:{self.port}/{self.database}"


class AppConfig:
    """应用配置类"""
    
    def __init__(self):
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.auth_type = os.getenv("AUTH_TYPE", "noop")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.uvicorn_log_level = os.getenv("UVICORN_LOG_LEVEL", "debug")
        self.database_echo = os.getenv("DATABASE_ECHO", "false").lower() == "true"


# 全局配置实例
database_config = DatabaseConfig()
app_config = AppConfig()

