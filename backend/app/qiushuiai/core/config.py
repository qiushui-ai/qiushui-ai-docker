import secrets
import warnings
import os
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    Field,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )
    API_V1_STR: str = "/api/v1"
    # 动态秘钥，每次服务启动时生成
    # SECRET_KEY: str = secrets.token_urlsafe(32)
     # 从环境变量读取SECRET_KEY
    SECRET_KEY: str = Field(
        default="dev-secret-key",
        description="用于JWT token加密的密钥"
    )
    
    # JWT token 过期时间配置
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24 * 8,  # 8 days = 11520 minutes
        description="JWT访问令牌过期时间(分钟)"
    )
    FRONTEND_HOST: str = "http://localhost:1420"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field(return_type=list[str])  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str
    SENTRY_DSN: HttpUrl | None = None
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @computed_field(return_type=PostgresDsn)  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: EmailStr | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field(return_type=bool)  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    EMAIL_TEST_USER: EmailStr = "test@example.com"
    FIRST_FIRST_SUPER_USERNAME: str
    FIRST_SUPERUSER_EMAIL: EmailStr
    FIRST_SUPERUSER_PASSWORD: str
    FIRST_SUPERUSER_PHONE: str | None = Field(default=None)
    
    # 外部 API 访问密钥
    API_KEY: str = Field(
        default="",
        description="外部API访问密钥"
    )

    # ZhipuAI 配置
    ZHIPUAI_API_KEY: str = Field(
        default="",
        description="ZhipuAI API密钥"
    )

    # 阿里云 DashScope 配置
    DASHSCOPE_API_KEY: str = Field(
        default="",
        description="阿里云 DashScope API密钥"
    )
    DASHSCOPE_EMBEDDING_MODEL: str = Field(
        default="text-embedding-v4",
        description="DashScope 嵌入模型名称"
    )

    # 阿里云 OSS 配置
    OSS_ACCESS_KEY_ID: str = Field(
        default="",
        description="阿里云 OSS Access Key ID"
    )
    OSS_ACCESS_KEY_SECRET: str = Field(
        default="",
        description="阿里云 OSS Access Key Secret"
    )
    OSS_ENDPOINT: str = Field(
        default="oss-cn-beijing.aliyuncs.com",
        description="阿里云 OSS Endpoint"
    )
    OSS_BUCKET_NAME: str = Field(
        default="",
        description="阿里云 OSS Bucket 名称"
    )

    # 文件上传配置
    MAX_FILE_SIZE: int = Field(
        default=50 * 1024 * 1024,  # 50MB
        description="最大文件上传大小(字节)"
    )
    MAX_FILES_COUNT: int = Field(
        default=50,
        description="最大上传文件数量"
    )
    MULTIPART_THRESHOLD: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        description="分片上传阈值(字节)"
    )
    PART_SIZE: int = Field(
        default=10 * 1024 * 1024,   # 10MB
        description="分片大小(字节)"
    )

    # 文档处理配置
    DOCUMENT_CHUNK_SIZE: int = Field(
        default=1000,
        description="文档分块大小(字符数)"
    )

    # 中间件配置
    MAX_BODY_SIZE: int = Field(
        default=10 * 1024,  # 10KB
        description="请求体最大大小(字节)"
    )
    CONTENT_LENGTH_LIMIT: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="内容长度限制(字节)"
    )
    SLOW_REQUEST_THRESHOLD: float = Field(
        default=1.0,
        description="慢请求阈值(秒)"
    )

    # 重试和超时配置
    DB_CONNECT_MAX_TRIES: int = Field(
        default=60 * 5,  # 5分钟
        description="数据库连接最大重试次数"
    )
    DB_CONNECT_WAIT_SECONDS: int = Field(
        default=1,
        description="数据库连接重试间隔(秒)"
    )

    # 分页配置
    DEFAULT_PAGE_SIZE: int = Field(
        default=2000,
        description="默认分页大小"
    )

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        # 生产环境必须设置安全的SECRET_KEY
        if self.ENVIRONMENT == "production" and self.SECRET_KEY.startswith("dev-"):
            raise ValueError(
                "生产环境必须设置安全的SECRET_KEY环境变量，不能使用默认的开发密钥"
            )
        
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self


settings = Settings()  # type: ignore
