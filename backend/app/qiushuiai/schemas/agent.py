import uuid as uuid_module
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, JSON, Column
from sqlalchemy import TIMESTAMP, Identity
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel


# 除了id、uuid、tenant_id、is_del、created_at、created_by、updated_at、updated_by之外的属性
# 属性定义与数据库模型一致
class AgentBase(SQLModel):
    name: str = Field(max_length=200, description="智能体名称")
    description: str | None = Field(default=None, description="描述")
    avatar: str | None = Field(default=None, description="头像URL")
    prompt_template: str | None = Field(default=None, description="提示词模板")
    llm_id: int | None = Field(default=None, description="关联模型ID")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int | None = Field(default=None, description="最大令牌数")
    capabilities: list[str] = Field(default_factory=list, sa_column=Column(JSONB), description="能力列表")
    settings: dict = Field(default_factory=dict, sa_column=Column(JSONB), description="配置设置")
    is_public: bool = Field(default=False, description="是否公开")
    usage_count: int = Field(default=0, description="使用次数")
    is_active: bool = Field(default=True, description="是否启用")
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSONB), description="标签列表")
    

# 创建时用
class AgentCreate(AgentBase):
    pass

# 更新时用，所有字段可选
class AgentUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=200, description="智能体名称")
    description: str | None = Field(default=None, description="描述")
    avatar: str | None = Field(default=None, description="头像URL")
    prompt_template: str | None = Field(default=None, description="提示词模板")
    llm_id: int | None = Field(default=None, description="关联模型ID")
    temperature: float | None = Field(default=None, description="温度参数")
    max_tokens: int | None = Field(default=None, description="最大令牌数")
    capabilities: list[str] | None = Field(default=None, description="能力列表")
    settings: dict | None = Field(default=None, description="配置设置")
    is_public: bool | None = Field(default=None, description="是否公开")
    usage_count: int | None = Field(default=None, description="使用次数")
    is_active: bool | None = Field(default=None, description="是否启用")
    
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSONB), description="标签列表")
    
    # 高级保存相关字段
    save_mode: str | None = Field(default="basic", description="保存模式：basic-普通保存，advanced-高级保存")
    knowledge_uuids: list[uuid_module.UUID] | None = Field(default=None, description="关联知识库UUID列表")
    tool_uuids: list[uuid_module.UUID] | None = Field(default=None, description="关联工具UUID列表")

# 数据库模型 - 表名为qsa_agent
class Agent(AgentBase, table=True):
    __tablename__ = "qsa_agent"
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()}, description="智能体ID")
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="智能体UUID")
    tenant_id: int = Field(description="所属租户ID")

    is_del: bool = Field(default=False, description="是否删除")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int = Field(description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int = Field(description="最后修改者")

# 列表或详情返回
class AgentPublic(AgentBase):
    id: int
    uuid: uuid_module.UUID
    tenant_id: int

    is_del: bool
    created_at: datetime
    created_by: int
    updated_at: datetime
    updated_by: int 

# 智能体知识库关联表
class AgentKnowledge(SQLModel, table=True):
    __tablename__ = "qsa_agent_knowledge"
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()}, description="关联ID")
    agent_id: int = Field(description="智能体ID")
    knowledge_id: int = Field(description="知识库ID")

# 智能体工具关联表
class AgentTools(SQLModel, table=True):
    __tablename__ = "qsa_agent_tools"
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()}, description="关联ID")
    agent_id: int = Field(description="智能体ID")
    tool_id: int = Field(description="工具ID") 

# 关联知识库信息模型
class AgentKnowledgeInfo(BaseModel):
    id: int  # 新增id字段
    uuid: uuid_module.UUID
    name: str

# 关联工具信息模型
class AgentToolInfo(BaseModel):
    uuid: uuid_module.UUID
    name: str
    tool_conf: dict = Field(default_factory=dict, sa_column=Column(JSONB), description="工具配置")
    tool_info: dict | None = Field(default=None, sa_column=Column(JSONB), description="工具信息")
    sub_type: str = Field(default="function", max_length=50, description="工具对接方式")
    tool_type: str = Field(default="function", max_length=50, description="工具类型")

# 智能体详情响应模型（包含关联信息）
class AgentDetailResponse(AgentPublic):
    knowledge_list: list[AgentKnowledgeInfo] = Field(default_factory=list, description="关联知识库列表")
    tool_list: list[AgentToolInfo] = Field(default_factory=list, description="关联工具列表")

# 智能体组织架构响应模型
class AgentOrganizationResponse(BaseModel):
    tree_data: list[dict] = Field(description="树形标签数据")
    agents: list[AgentPublic] = Field(description="所有智能体列表") 