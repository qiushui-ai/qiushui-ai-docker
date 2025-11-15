import uuid as uuid_module
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, JSON, Column
from sqlalchemy import TIMESTAMP, Identity
from pydantic import BaseModel


# 除了id、uuid、tenant_id、is_del、created_at、created_by、updated_at、updated_by之外的属性
# 属性定义与数据库模型一致
class PromptsLibBase(SQLModel):
    title: str = Field(max_length=200, description="标题")
    prompts: str = Field(description="提示词内容")
    remark: Optional[str] = Field(default=None, description="备注")
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON), description="标签列表")
    is_active: bool = Field(default=True, description="是否启用")
    is_public: bool = Field(default=False, description="是否公开")


# 无任何字段，只有pass，创建的时候需要对某个字段做赋值，可以在这里配置
class PromptsLibCreate(PromptsLibBase):
    pass


# 除了id、uuid、tenant_id、is_del、created_at、created_by、updated_at、updated_by之外的属性
# 属性都可为None
class PromptsLibUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=200, description="标题")
    prompts: str | None = Field(default=None, description="提示词内容")
    remark: str | None = Field(default=None, description="备注")
    tags: list[str] | None = Field(default=None, description="标签列表")
    is_active: bool | None = Field(default=None, description="是否启用")
    is_public: bool | None = Field(default=None, description="是否公开")


# 数据库模型 - 表名为qsa_prompts_libs
# 包含id、uuid、tenant_id、is_del、created_at、created_by、updated_at、updated_by字段，如果表结构有这些字段，则需要在这里定义
class PromptsLib(PromptsLibBase, table=True):
    __tablename__ = "qsa_prompts_libs"
    
    # 系统字段
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()})
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="提示词库UUID")
    tenant_id: int = Field(description="所属租户ID")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")


# 列表或者详情返回的属性
class PromptsLibPublic(PromptsLibBase):
    id: int
    uuid: uuid_module.UUID
    tenant_id: int
  
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int 