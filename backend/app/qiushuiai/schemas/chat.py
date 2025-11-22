import uuid as uuid_module
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, JSON, Column
from sqlalchemy import TIMESTAMP, Identity
from sqlalchemy.dialects.postgresql import JSONB

# 对话表 - qsa_chat_conversation
class ChatConversationBase(SQLModel):
    title: Optional[str] = Field(default=None, max_length=500, description="对话标题")
    summary: Optional[str] = Field(default=None, description="对话摘要")
    status: str = Field(default="active", max_length=20, description="状态")
    message_count: int = Field(default=0, description="消息数量")
    total_tokens: int = Field(default=0, description="总令牌数")
    total_cost: Optional[float] = Field(default=None, description="总成本")
    llm_uuid: Optional[uuid_module.UUID] = Field(default=None, description="模型UUID")
    agent_uuid: Optional[uuid_module.UUID] = Field(default=None, description="智能体UUID")
    prompt_uuid: Optional[uuid_module.UUID] = Field(default=None, description="系统提示词UUID")
    extra_data: dict = Field(default_factory=dict, sa_column=Column(JSONB), description="额外数据")
    last_message_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)), description="最后消息时间")

class ChatConversationCreate(ChatConversationBase):
    uuid: Optional[uuid_module.UUID] = Field(default=None, description="对话UUID(可选,不传则自动生成)")

class ChatConversationUpdate(SQLModel):
    title: Optional[str] = Field(default=None, max_length=500, description="对话标题")
    summary: Optional[str] = Field(default=None, description="对话摘要")
    status: Optional[str] = Field(default=None, max_length=20, description="状态")
    message_count: Optional[int] = Field(default=None, description="消息数量")
    total_tokens: Optional[int] = Field(default=None, description="总令牌数")
    total_cost: Optional[float] = Field(default=None, description="总成本")
    llm_uuid: Optional[uuid_module.UUID] = Field(default=None, description="模型UUID")
    extra_data: Optional[dict] = Field(default=None, description="额外数据")
    last_message_at: Optional[datetime] = Field(default=None, description="最后消息时间")

class ChatConversation(ChatConversationBase, table=True):
    __tablename__ = "qsa_chat_conversation"
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()}, description="对话ID")
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="对话UUID")
    tenant_id: int = Field(description="所属租户ID")

    agent_uuid: Optional[uuid_module.UUID] = Field(default=None, description="智能体UUID")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")

class ChatConversationPublic(ChatConversationBase):
    id: int
    uuid: uuid_module.UUID
    tenant_id: int

    agent_uuid: Optional[uuid_module.UUID]
    llm_uuid: Optional[uuid_module.UUID]
    prompt_uuid: Optional[uuid_module.UUID]
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
    agent: Optional[dict] = None  # 添加智能体信息字段

# 消息表 - qsa_chat_message
class ChatMessageBase(SQLModel):
    role: str = Field(max_length=20, description="角色(user/assistant/system/tool)")
    content: str = Field(description="消息内容")
    content_type: str = Field(default="text", max_length=20, description="内容类型")
    tool_calls: list = Field(default_factory=list, sa_column=Column(JSONB), description="工具调用记录")
    tool_results: list = Field(default_factory=list, sa_column=Column(JSONB), description="工具执行结果")
    tokens: int = Field(default=0, description="令牌数")
    cost: float = Field(default=0.0, description="成本")
    extra_data: dict = Field(default_factory=dict, sa_column=Column(JSONB), description="额外数据")
    parent_message_id: Optional[int] = Field(default=None, description="父消息ID")

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessageUpdate(SQLModel):
    role: Optional[str] = Field(default=None, max_length=20, description="角色")
    content: Optional[str] = Field(default=None, description="消息内容")
    content_type: Optional[str] = Field(default=None, max_length=20, description="内容类型")
    tool_calls: Optional[list] = Field(default=None, description="工具调用记录")
    tool_results: Optional[list] = Field(default=None, description="工具执行结果")
    tokens: Optional[int] = Field(default=None, description="令牌数")
    cost: Optional[float] = Field(default=None, description="成本")
    extra_data: Optional[dict] = Field(default=None, description="额外数据")
    parent_message_id: Optional[int] = Field(default=None, description="父消息ID")

class ChatMessage(ChatMessageBase, table=True):
    __tablename__ = "qsa_chat_message"
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()}, description="消息ID")
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="消息UUID")
    conversation_id: int = Field(description="所属对话ID")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")

class ChatMessagePublic(ChatMessageBase):
    id: int
    uuid: uuid_module.UUID
    conversation_id: int
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int 


# ==================== 文档表相关类 ====================

# 除了id、uuid、created_at、created_by、updated_at、updated_by之外的属性
class ChatDocumentBase(SQLModel):
   
    chat_conversation_id: int | None = Field(default=None, description="所属对话ID")
    chat_conversation_uuid: uuid_module.UUID | None = Field(default=None, description="所属对话UUID")
    title: str = Field(max_length=500, description="文档标题")
    filename: str | None = Field(default=None, max_length=255, description="文件名")
    file_type: str = Field(default="text", max_length=50, description="文件类型")
    file_size: int = Field(default=0, description="文件大小")
    content: str | None = Field(default=None, description="文档内容")
    extra_data: dict = Field(default_factory=dict, sa_column=Column(JSON), description="文档元数据")
    source_url: str | None = Field(default=None, description="来源URL")
    hash: str | None = Field(default=None, max_length=64, description="内容哈希")
    chunk_count: int = Field(default=0, description="分块数量")
    token_count: int = Field(default=0, description="令牌数")
    status: str = Field(default="processed", max_length=20, description="处理状态")
    extraction_tool: str | None = Field(default=None, max_length=100, description="提取工具")
    embedding_model: str | None = Field(default=None, max_length=100, description="向量转换模型")
    processed_at: datetime | None = Field(default=None, description="处理时间")


# 无任何字段，只有pass，创建的时候需要对某个字段做赋值，可以在这里配置
class ChatDocumentCreate(ChatDocumentBase):
    pass


# 除了id、uuid、created_at、created_by、updated_at、updated_by之外的属性
# 属性都可为None
class ChatDocumentUpdate(SQLModel):
   
    chat_conversation_id: int | None = Field(default=None, description="所属对话ID")
    chat_conversation_uuid: uuid_module.UUID | None = Field(default=None, description="所属对话UUID")
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
    status: str | None = Field(default=None, max_length=20, description="处理状态")
    extraction_tool: str | None = Field(default=None, max_length=100, description="提取工具")
    embedding_model: str | None = Field(default=None, max_length=100, description="向量转换模型")
    processed_at: datetime | None = Field(default=None, description="处理时间")


# 数据库模型 - 表名为qsa_kb_document
class ChatDocument(ChatDocumentBase, table=True):
    __tablename__ = "qsa_chat_document"
    
    # 系统字段
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()})
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="文档UUID")
    tenant_id: int = Field(description="所属租户ID")  # 新增tenant_id字段
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")


# 列表或者详情返回的属性
class ChatDocumentPublic(ChatDocumentBase):
    id: int
    uuid: uuid_module.UUID
    tenant_id: int  # 新增tenant_id字段
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int
