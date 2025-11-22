import uuid as uuid_module
from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlmodel import Field, SQLModel, JSON, Column
from sqlalchemy import TIMESTAMP, Identity, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel


# 白板基础模型
class WhiteboardBase(SQLModel):
    title: str = Field(max_length=255, default="未命名白板", description="白板标题")
    description: Optional[str] = Field(default=None, description="白板描述")
    snapshot: Optional[dict] = Field(default=None, sa_column=Column(JSONB), description="白板快照数据")
    thumbnail_url: Optional[str] = Field(default=None, max_length=512, description="缩略图URL")
    background_color: str = Field(default="#ffffff", max_length=20, description="背景颜色")
    is_public: int = Field(default=0, description="是否公开")
    view_count: int = Field(default=0, description="查看次数")
    status: int = Field(default=1, description="状态")


class WhiteboardCreate(WhiteboardBase):
    pass


class WhiteboardUpdate(SQLModel):
    title: Optional[str] = Field(default=None, max_length=255, description="白板标题")
    description: Optional[str] = Field(default=None, description="白板描述")
    snapshot: Optional[dict] = Field(default=None, description="白板快照数据")
    thumbnail_url: Optional[str] = Field(default=None, max_length=512, description="缩略图URL")
    background_color: Optional[str] = Field(default=None, max_length=20, description="背景颜色")
    is_public: Optional[int] = Field(default=None, description="是否公开")
    view_count: Optional[int] = Field(default=None, description="查看次数")
    status: Optional[int] = Field(default=None, description="状态")


# 白板数据库模型
class Whiteboard(WhiteboardBase, table=True):
    __tablename__ = "qsa_note_whiteboard"
    
    # 系统字段
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()})
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="白板UUID")
    tenant_id: int = Field(description="所属租户ID")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")


# 白板公开返回模型
class WhiteboardPublic(WhiteboardBase):
    id: int
    uuid: uuid_module.UUID
    tenant_id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int


# 白板笔记关联基础模型
class WhiteboardNoteBase(SQLModel):
    whiteboard_uuid: uuid_module.UUID = Field(description="白板UUID")
    note_uuid: uuid_module.UUID = Field(description="笔记UUID")
    shape_id: str = Field(max_length=100, description="形状ID")
    shape_type: str = Field(default="note-card", max_length=50, description="形状类型")
    position_x: Decimal = Field(default=Decimal("0"), sa_column=Column(Numeric(10, 2)), description="X坐标")
    position_y: Decimal = Field(default=Decimal("0"), sa_column=Column(Numeric(10, 2)), description="Y坐标")
    width: Decimal = Field(default=Decimal("300"), sa_column=Column(Numeric(10, 2)), description="宽度")
    height: Decimal = Field(default=Decimal("200"), sa_column=Column(Numeric(10, 2)), description="高度")
    rotation: Decimal = Field(default=Decimal("0"), sa_column=Column(Numeric(10, 2)), description="旋转角度")
    z_index: int = Field(default=0, description="层级")
    is_locked: int = Field(default=0, description="是否锁定")
    note_snapshot: Optional[dict] = Field(default=None, sa_column=Column(JSONB), description="笔记快照")
    status: int = Field(default=1, description="状态")


class WhiteboardNoteCreate(WhiteboardNoteBase):
    pass


class WhiteboardNoteUpdate(SQLModel):
    whiteboard_uuid: Optional[uuid_module.UUID] = Field(default=None, description="白板UUID")
    note_uuid: Optional[uuid_module.UUID] = Field(default=None, description="笔记UUID")
    shape_id: Optional[str] = Field(default=None, max_length=100, description="形状ID")
    shape_type: Optional[str] = Field(default=None, max_length=50, description="形状类型")
    position_x: Optional[Decimal] = Field(default=None, description="X坐标")
    position_y: Optional[Decimal] = Field(default=None, description="Y坐标")
    width: Optional[Decimal] = Field(default=None, description="宽度")
    height: Optional[Decimal] = Field(default=None, description="高度")
    rotation: Optional[Decimal] = Field(default=None, description="旋转角度")
    z_index: Optional[int] = Field(default=None, description="层级")
    is_locked: Optional[int] = Field(default=None, description="是否锁定")
    note_snapshot: Optional[dict] = Field(default=None, description="笔记快照")
    status: Optional[int] = Field(default=None, description="状态")


# 白板笔记关联数据库模型
class WhiteboardNote(WhiteboardNoteBase, table=True):
    __tablename__ = "qsa_note_whiteboard_note"
    
    # 系统字段
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()})
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="关联UUID")
    tenant_id: int = Field(description="所属租户ID")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")


# 白板笔记关联公开返回模型
class WhiteboardNotePublic(WhiteboardNoteBase):
    id: int
    uuid: uuid_module.UUID
    tenant_id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
