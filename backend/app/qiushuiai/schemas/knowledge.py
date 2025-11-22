import uuid as uuid_module
from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlmodel import Field, SQLModel, JSON, Column, Text
from sqlalchemy import TIMESTAMP, Identity, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel


# 除了id、uuid、tenant_id、is_del、created_at、created_by、updated_at、updated_by之外的属性
# 属性定义与数据库模型一致
class KbKnowledgeBase(SQLModel):
    name: str = Field(max_length=200, description="知识库名称")
    description: str | None = Field(default=None, description="知识库描述")
    # 将 category 改为可选字段，并设置默认值
    category: str | None = Field(default="default", max_length=50, description="知识库分类")
    embedding_model: str = Field(
        default="", 
        max_length=100, 
        description="嵌入模型"
    )
    chunk_size: int = Field(default=1000, description="分块大小")
    chunk_overlap: int = Field(default=200, description="分块重叠")
    document_count: int = Field(default=0, description="文档数量")
    total_tokens: int = Field(default=0, description="总令牌数")
    index_status: str = Field(default="ready", max_length=20, description="索引状态")
    last_indexed: datetime | None = Field(default=None, description="最后索引时间")
    is_active: bool = Field(default=True, description="是否启用")
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSONB), description="标签列表")
    settings: dict = Field(default_factory=dict, sa_column=Column(JSONB), description="配置设置")


# 无任何字段，只有pass，创建的时候需要对某个字段做赋值，可以在这里配置
class KbKnowledgeCreate(KbKnowledgeBase):
    pass


# 除了id、uuid、tenant_id、is_del、created_at、created_by、updated_at、updated_by之外的属性
# 属性都可为None
class KbKnowledgeUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=200, description="知识库名称")
    description: str | None = Field(default=None, description="知识库描述")
    category: str | None = Field(default=None, max_length=50, description="知识库分类")
    tags: list[str] | None = Field(default=None, description="标签列表")
    embedding_model: str | None = Field(default=None, max_length=100, description="嵌入模型")
    chunk_size: int | None = Field(default=None, description="分块大小")
    chunk_overlap: int | None = Field(default=None, description="分块重叠")
    settings: dict | None = Field(default=None, description="配置设置")
    is_active: bool | None = Field(default=None, description="是否启用")


# 数据库模型 - 表名为qsa_kb_knowledge
# 包含id、uuid、tenant_id、is_del、created_at、created_by、updated_at、updated_by字段，如果表结构有这些字段，则需要在这里定义
class KbKnowledge(KbKnowledgeBase, table=True):
    __tablename__ = "qsa_kb_knowledge"
    
    # 系统字段
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()})
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="知识库UUID")
    tenant_id: int = Field(description="所属租户ID")
    is_del: bool = Field(default=False, description="是否删除")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")


# 列表或者详情返回的属性
class KbKnowledgePublic(KbKnowledgeBase):
    id: int
    uuid: uuid_module.UUID
    tenant_id: int
    is_del: bool
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int


# ==================== 文档表相关类 ====================

# 除了id、uuid、created_at、created_by、updated_at、updated_by之外的属性
class KbDocumentBase(SQLModel):
    knowledge_base_id: int | None = Field(default=None, description="所属知识库ID")
   
    title: str = Field(max_length=500, description="文档标题")
    filename: str | None = Field(default=None, max_length=255, description="文件名")
    file_type: str = Field(default="text", max_length=50, description="文件类型")
    file_size: int = Field(default=0, description="文件大小")
    content: str | None = Field(default=None, description="文档内容")
    extra_data: dict = Field(default_factory=dict, sa_column=Column(JSONB), description="文档元数据")
    source_url: str | None = Field(default=None, description="来源URL")
    hash: str | None = Field(default=None, max_length=64, description="内容哈希")
    chunk_count: int = Field(default=0, description="分块数量")
    token_count: int = Field(default=0, description="令牌数")
    status: str = Field(default="processed", max_length=20, description="处理状态")
    extraction_tool: str | None = Field(default=None, max_length=100, description="提取工具")
    embedding_model: str | None = Field(default=None, max_length=100, description="向量转换模型")
    processed_at: datetime | None = Field(default=None, description="处理时间")


# 无任何字段，只有pass，创建的时候需要对某个字段做赋值，可以在这里配置
class KbDocumentCreate(KbDocumentBase):
    pass


# 除了id、uuid、created_at、created_by、updated_at、updated_by之外的属性
# 属性都可为None
class KbDocumentUpdate(SQLModel):
    knowledge_base_id: int | None = Field(default=None, description="所属知识库ID")

    title: str | None = Field(default=None, max_length=500, description="文档标题")
    filename: str | None = Field(default=None, max_length=255, description="文件名")
    file_type: str | None = Field(default=None, max_length=50, description="文件类型")
    file_size: int | None = Field(default=None, description="文件大小")
    content: str | None = Field(default=None, description="文档内容")
    extra_data: dict | None = Field(default=None, description="文档元数据")
    source_url: str | None = Field(default=None, description="来源URL")
    hash: str | None = Field(default=None, max_length=64, description="内容哈希")
    chunk_count: int | None = Field(default=None, description="分块数量")
    token_count: int | None = Field(default=None, description="令牌数")
    extraction_tool: str | None = Field(default=None, max_length=100, description="提取工具")
    embedding_model: str | None = Field(default=None, max_length=100, description="向量转换模型")
    status: str | None = Field(default=None, max_length=20, description="处理状态")
    processed_at: datetime | None = Field(default=None, description="处理时间")


# 数据库模型 - 表名为qsa_kb_document
class KbDocument(KbDocumentBase, table=True):
    __tablename__ = "qsa_kb_document"
    
    # 系统字段
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()})
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="文档UUID")
    tenant_id: int = Field(description="所属租户ID")  # 新增tenant_id字段
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")


# 列表或者详情返回的属性
class KbDocumentPublic(KbDocumentBase):
    id: int
    uuid: uuid_module.UUID
    tenant_id: int  # 新增tenant_id字段
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int


# ==================== 文档块表相关类 ====================

# 除了id、uuid、created_at、created_by、updated_at、updated_by之外的属性
class KbChunkBase(SQLModel):
    document_id: int = Field(description="所属文档ID")
    content: str = Field(description="分块内容")
    # 向量嵌入现在存储在 PGVector 中，这里不再需要
    embedding: str | None = Field(
        default=None, 
        sa_column=Column(Text), 
        description="向量嵌入（已废弃，现在存储在PGVector中）"
    )
    extra_data: dict = Field(default_factory=dict, sa_column=Column(JSONB), description="分块元数据")
    position: int = Field(default=0, description="位置序号")
    token_count: int = Field(default=0, description="令牌数")
    similarity_threshold: Decimal = Field(
        default=Decimal("0.8000"), 
        sa_column=Column(Numeric(5, 4)), 
        description="相似度阈值"
    )


# 无任何字段，只有pass，创建的时候需要对某个字段做赋值，可以在这里配置
class KbChunkCreate(KbChunkBase):
    pass


# 除了id、uuid、created_at、created_by、updated_at、updated_by之外的属性
# 属性都可为None
class KbChunkUpdate(SQLModel):
    document_id: int | None = Field(default=None, description="所属文档ID")
    content: str | None = Field(default=None, description="分块内容")
    embedding: list[float] | None = Field(default=None, description="向量嵌入")
    extra_data: dict | None = Field(default=None, description="分块元数据")
    position: int | None = Field(default=None, description="位置序号")
    token_count: int | None = Field(default=None, description="令牌数")
    similarity_threshold: Decimal | None = Field(default=None, description="相似度阈值")


# 数据库模型 - 表名为qsa_kb_chunk
class KbChunk(KbChunkBase, table=True):
    __tablename__ = "qsa_kb_chunk"
    
    # 系统字段
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()})
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="分块UUID")
    tenant_id: int = Field(description="所属租户ID")  # 新增tenant_id字段
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")


# 列表或者详情返回的属性
class KbChunkPublic(KbChunkBase):
    id: int
    uuid: uuid_module.UUID
    tenant_id: int  # 新增tenant_id字段
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int

    