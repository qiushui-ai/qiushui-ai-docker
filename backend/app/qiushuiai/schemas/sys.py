import uuid as uuid_module
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel
from sqlalchemy import TIMESTAMP, Identity, JSON, Column
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel


# 除了id、uuid、created_at、created_by、updated_at、updated_by之外的属性
# 属性定义与数据库模型一致
class SysTagsBase(SQLModel):
    puuid: Optional[str] = Field(default=None, max_length=100, description="父级UUID")
    name: str = Field(max_length=300, description="名称")
    pname: Optional[str] = Field(default="active", max_length=300, description="父名称")
    remark: Optional[str] = Field(default="active", max_length=300, description="备注")
    sortorder: Optional[int] = Field(default=None, description="排序")
    flag: str = Field(default="active", max_length=20, description="类别，note/agent/knowledge/tool/conversation")


# 无任何字段，只有pass，创建的时候需要对某个字段做赋值，可以在这里配置
class SysTagsCreate(SysTagsBase):
    pass


# 除了id、uuid、created_at、created_by、updated_at、updated_by之外的属性
# 属性都可为None
class SysTagsUpdate(SQLModel):
    puuid: str | None = Field(default=None, max_length=100, description="父级UUID")
    name: str | None = Field(default=None, max_length=300, description="名称")
    pname: str | None = Field(default=None, max_length=300, description="父名称")
    remark: str | None = Field(default=None, max_length=300, description="备注")
    sortorder: int | None = Field(default=None, description="排序")
    flag: str | None = Field(default=None, max_length=20, description="类别，note/agent/knowledge/tool/conversation")


# 数据库模型 - 表名为qsa_sys_tags
# 包含id、uuid、created_at、created_by、updated_at、updated_by字段，如果表结构有这些字段，则需要在这里定义
class SysTags(SysTagsBase, table=True):
    __tablename__ = "qsa_sys_tags"
    
    # 系统字段
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()})
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="标签UUID")
    tenant_id: int = Field(description="所属租户ID")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=TIMESTAMP(timezone=True), description="创建时间")
    created_by: Optional[int] = Field(default=None, description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=TIMESTAMP(timezone=True), description="更新时间")
    updated_by: Optional[int] = Field(default=None, description="最后修改者")


# 列表或者详情返回的属性
class SysTagsPublic(SysTagsBase):
    id: int
    uuid: uuid_module.UUID
    created_at: datetime
    created_by: Optional[int]
    updated_at: datetime
    updated_by: Optional[int] 