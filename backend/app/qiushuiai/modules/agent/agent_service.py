from typing import Optional
import uuid as uuid_module

from sqlmodel import select, Session

from qiushuiai.core.db_filters import apply_common_filters
from qiushuiai.core.exceptions import ResourceNotFoundException
from qiushuiai.schemas.agent import (
    Agent,
    AgentKnowledge,
    AgentTools,
    AgentDetailResponse,
    AgentKnowledgeInfo,
    AgentToolInfo,
)
from qiushuiai.modules.user.deps import CurrentUser


def get_agent_detail(
    session: Session,
    current_user: CurrentUser,
    uuid: Optional[uuid_module.UUID] = None,
    id: Optional[int] = None
) -> AgentDetailResponse:
    """
    获取智能体详情，包括关联的知识库和工具信息。
    
    Args:
        session: 数据库会话
        current_user: 当前用户
        uuid: 智能体UUID（可选）
        id: 智能体ID（可选）
        
    Returns:
        AgentDetailResponse: 智能体详情响应对象
        
    Raises:
        ResourceNotFoundException: 当智能体不存在时抛出
        ValueError: 当既没有提供uuid也没有提供id时抛出
    """
    from qiushuiai.schemas.knowledge import KbKnowledge
    from qiushuiai.schemas.tools import Tools
    
    # 验证参数
    if uuid is None and id is None:
        raise ValueError("必须提供uuid或id参数")
    
    # 查询智能体基本信息
    if id is not None:
        statement = select(Agent).where(Agent.id == id)
    else:
        statement = select(Agent).where(Agent.uuid == uuid)
    
    statement = apply_common_filters(
        statement=statement,
        model=Agent,
        current_user=current_user
    )
    agent = session.exec(statement).first()
    if not agent:
        raise ResourceNotFoundException(message="智能体不存在")
    
    # 获取关联的知识库列表
    knowledge_list = _get_agent_knowledge_list(session, agent.id)
    
    # 获取关联的工具列表
    tool_list = _get_agent_tool_list(session, agent.id)
    
    # 构建详情响应
    agent_detail = AgentDetailResponse(
        **agent.model_dump(),
        knowledge_list=knowledge_list,
        tool_list=tool_list
    )
    
    return agent_detail


def get_agent_by_uuid(
    session: Session,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Optional[Agent]:
    """
    根据UUID获取智能体基本信息。
    
    Args:
        session: 数据库会话
        current_user: 当前用户
        uuid: 智能体UUID
        
    Returns:
        Optional[Agent]: 智能体对象，如果不存在则返回None
    """
    statement = select(Agent).where(Agent.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=Agent,
        current_user=current_user
    )
    return session.exec(statement).first()





def _get_agent_knowledge_list(session: Session, agent_id: int) -> list[AgentKnowledgeInfo]:
    """
    获取智能体关联的知识库列表。
    
    Args:
        session: 数据库会话
        agent_id: 智能体ID
        
    Returns:
        list[AgentKnowledgeInfo]: 知识库信息列表
    """
    from qiushuiai.schemas.knowledge import KbKnowledge
    
    knowledge_list = []
    agent_knowledge_relations = session.exec(
        select(AgentKnowledge).where(AgentKnowledge.agent_id == agent_id)
    ).all()
    
    for relation in agent_knowledge_relations:
        knowledge = session.exec(
            select(KbKnowledge).where(
                KbKnowledge.id == relation.knowledge_id,
                KbKnowledge.is_del == False
            )
        ).first()
        if knowledge:
            knowledge_list.append(AgentKnowledgeInfo(
                id=knowledge.id,
                uuid=knowledge.uuid,
                name=knowledge.name
            ))
    
    return knowledge_list


def _get_agent_tool_list(session: Session, agent_id: int) -> list[AgentToolInfo]:
    """
    获取智能体关联的工具列表。
    
    Args:
        session: 数据库会话
        agent_id: 智能体ID
        
    Returns:
        list[AgentToolInfo]: 工具信息列表
    """
    from qiushuiai.schemas.tools import Tools
    
    tool_list = []
    agent_tool_relations = session.exec(
        select(AgentTools).where(AgentTools.agent_id == agent_id)
    ).all()
    
    for relation in agent_tool_relations:
        tool = session.exec(
            select(Tools).where(Tools.id == relation.tool_id)
        ).first()
        if tool:
            tool_list.append(AgentToolInfo(
                uuid=tool.uuid,
                name=tool.name,
                tool_conf=tool.tool_conf,
                tool_info=tool.tool_info,
                sub_type=tool.sub_type,
                tool_type=tool.tool_type
            ))
    
    return tool_list 