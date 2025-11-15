import uuid as uuid_module
from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlmodel import Field, SQLModel, JSON, Column
from sqlalchemy import TIMESTAMP, Identity, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel

# 除了id、uuid、tenant_id、created_at、created_by、updated_at、updated_by之外的属性
# 属性定义与数据库模型一致
class ToolsBase(SQLModel):
    name: str = Field(max_length=200, description="工具名称")
    description: str | None = Field(default=None, description="工具描述")
    category: str | None = Field(default=None, max_length=50, description="工具分类")  # 工具分类，可为空
    icon: str | None = Field(default=None, description="工具图标")
    tool_type: str = Field(default="function", max_length=50, description="工具类型(function/api/webhook/mcp)")
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON), description="标签")
    last_used_at: datetime | None = Field(default=None, description="最后使用时间")
    is_active: bool = Field(default=True, description="是否启用")
    tool_conf: dict = Field(default_factory=dict, sa_column=Column(JSON), description="工具配置")
    tool_info: dict | None = Field(default=None, sa_column=Column(JSONB), description="工具信息")
    sub_type: str = Field(default="function", max_length=50, description="工具对接方式")

# 创建时用
class ToolsCreate(ToolsBase):
    pass

# 更新时用，所有字段可选
class ToolsUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=200, description="工具名称")
    description: str | None = Field(default=None, description="工具描述")
    category: str | None = Field(default=None, max_length=50, description="工具分类，可为空")
    icon: str | None = Field(default=None, description="工具图标")
    tool_type: str | None = Field(default=None, max_length=50, description="工具类型(function/api/webhook/mcp)")
    tags: list[str] | None = Field(default=None, description="标签")
    last_used_at: datetime | None = Field(default=None, description="最后使用时间")
    is_active: bool | None = Field(default=None, description="是否启用")
    tool_conf: dict | None = Field(default=None, description="工具配置")
    tool_info: dict | None = Field(default=None, description="工具信息")
    sub_type: str | None = Field(default=None, max_length=50, description="工具对接方式")

# 数据库模型 - 表名为qsa_tools
class Tools(ToolsBase, table=True):
    __tablename__ = "qsa_tools"
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()}, description="工具ID")
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="工具UUID")
    tenant_id: int = Field(description="所属租户ID")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")

# 列表或详情返回
class ToolsPublic(ToolsBase):
    id: int
    uuid: uuid_module.UUID
    tenant_id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int 

# MCP 信息响应模型

class ToolsMCPResponse(BaseModel):
    tool_info: ToolsPublic
    tools: list[dict] = Field(default_factory=list, description="可用工具列表")
    resources: list[dict] = Field(default_factory=list, description="可用资源列表")
    prompts: list[dict] = Field(default_factory=list, description="可用提示列表")