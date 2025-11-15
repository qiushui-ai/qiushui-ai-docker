import uuid as uuid_module
from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlmodel import Field, SQLModel, JSON, Column
from sqlalchemy import TIMESTAMP, Identity, Numeric, text
from pydantic import BaseModel

# AI厂商基类
class AIProviderBase(SQLModel):
    name: str = Field(max_length=100, description="厂商标识名称")
    display_name: str = Field(max_length=100, description="厂商显示名称")
    description: str | None = Field(default=None, max_length=255, description="厂商描述")
    website: str | None = Field(default=None, max_length=255, description="官方网站")
    logo_url: str | None = Field(default=None, max_length=300, description="Logo图片URL")
    api_base_url: str | None = Field(default=None, max_length=300, description="API基础地址")
    auth_config: dict = Field(default_factory=dict, sa_column=Column(JSON), description="认证配置信息")
    is_active: bool = Field(default=True, description="是否启用")
    api_secret: str | None = Field(default=None, max_length=300, description="API密钥")

# AI厂商创建模型
class AIProviderCreate(AIProviderBase):
    pass

# AI厂商更新模型
class AIProviderUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=100, description="厂商标识名称")
    display_name: str | None = Field(default=None, max_length=100, description="厂商显示名称")
    description: str | None = Field(default=None, max_length=255, description="厂商描述")
    website: str | None = Field(default=None, max_length=255, description="官方网站")
    logo_url: str | None = Field(default=None, max_length=300, description="Logo图片URL")
    api_base_url: str | None = Field(default=None, max_length=300, description="API基础地址")
    auth_config: dict | None = Field(default=None, description="认证配置信息")
    is_active: bool | None = Field(default=None, description="是否启用")
    api_secret: str | None = Field(default=None, max_length=300, description="API密钥")

# AI厂商数据库模型
class AIProvider(AIProviderBase, table=True):
    __tablename__ = "qsa_ai_provider"
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()}, description="厂商ID")
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="厂商UUID")
    tenant_id: int = Field(description="所属租户ID")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")

# AI厂商公共响应模型
class AIProviderPublic(AIProviderBase):
    id: int
    uuid: uuid_module.UUID
    tenant_id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int

# AI模型基类
class AIModelBase(SQLModel):
    provider_id: int = Field(description="所属厂商ID")
    llm_id: str = Field(max_length=200, description="模型标识符")
    name: str = Field(max_length=200, description="模型名称")
    display_name: str = Field(max_length=200, description="显示名称")
    llm_type: list = Field(default_factory=list, sa_column=Column(JSON), description="模型类型列表")
    max_tokens: int | None = Field(default=None, description="最大令牌数")
    context_window: int | None = Field(default=None, description="上下文窗口大小")
    is_active: bool = Field(default=True, description="是否启用")
    is_default: bool = Field(default=False, description="是否默认")

# AI模型创建模型
class AIModelCreate(AIModelBase):
    pass

# AI模型更新模型
class AIModelUpdate(SQLModel):
    provider_id: int | None = Field(default=None, description="所属厂商ID")
    llm_id: str | None = Field(default=None, max_length=200, description="模型标识符")
    name: str | None = Field(default=None, max_length=200, description="模型名称")
    display_name: str | None = Field(default=None, max_length=200, description="显示名称")
    llm_type: list | None = Field(default=None, description="模型类型列表")
    max_tokens: int | None = Field(default=None, description="最大令牌数")
    context_window: int | None = Field(default=None, description="上下文窗口大小")
    is_active: bool | None = Field(default=None, description="是否启用")
    is_default: bool | None = Field(default=None, description="是否默认")

# AI模型数据库模型
class AIModel(AIModelBase, table=True):
    __tablename__ = "qsa_ai_model"
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()}, description="模型ID")
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="模型UUID")
    tenant_id: int = Field(description="所属租户ID")
    llm_type: list = Field(default_factory=list, sa_column=Column(JSON, server_default=text("'[]'::jsonb")), description="模型类型列表")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")

# AI模型公共响应模型
class AIModelPublic(AIModelBase):
    id: int
    uuid: uuid_module.UUID
    tenant_id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    provider_name: str | None = None
    provider_api_base_url: str | None = None
    provider_api_secret: str | None = None

# AI模型详情响应模型（包含厂商信息）
class AIModelDetailResponse(BaseModel):
    llm_info: AIModelPublic
    provider_info: AIProviderPublic | None = None 