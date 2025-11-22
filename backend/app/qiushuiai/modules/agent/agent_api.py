from typing import Any, Annotated
from datetime import datetime
import uuid as uuid_module

from fastapi import APIRouter, Body
from sqlmodel import select

from qiushuiai.modules.user.deps import CurrentUser, SessionDep
from qiushuiai.core.db_filters import (
    apply_common_filters,
    apply_pagination,
    build_order_by,
    get_count_query,
    update_common_fields,
    apply_keyword_search
)
from qiushuiai.core.response import (
    BaseResponse,
    success_response,
    page_response,
    PageResponse,
    ResponseCode,
    ResponseMessage,
)
from qiushuiai.core.exceptions import ResourceNotFoundException
from qiushuiai.schemas.agent import (
    Agent,
    AgentCreate,
    AgentPublic,
    AgentUpdate,
    AgentKnowledge,
    AgentTools,
    AgentDetailResponse,
    AgentKnowledgeInfo,
    AgentToolInfo,
    AgentOrganizationResponse,
)
from qiushuiai.modules.agent.agent_service import get_agent_detail, get_agent_by_uuid
from qiushuiai.modules.sys.sys_tags_service import SysTagsService

router = APIRouter(prefix="/agent", tags=["agent"])

@router.post("/page", response_model=BaseResponse[PageResponse[AgentPublic]])
def page_agents(
    session: SessionDep,
    current_user: CurrentUser,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取智能体列表。"""
    page = request_data.get("page", 1)
    rows = request_data.get("rows", 20)
    keyword = request_data.get("keyword")
    statement = select(Agent)
    statement = apply_common_filters(
        statement=statement,
        model=Agent,
        current_user=current_user
    )
    statement = apply_keyword_search(
        statement=statement,
        model=Agent,
        keyword=keyword,
        search_fields=["name", "description", "capabilities", "tags"]
    )
    count_statement = get_count_query(statement, Agent)
    count = session.exec(count_statement).one()
    statement = build_order_by(
        statement=statement,
        model=Agent,
        order_by="id",
        order_direction="desc"
    )
    statement, _, _ = apply_pagination(
        statement=statement,
        page=page,
        page_size=rows
    )
    agents = session.exec(statement).all()
    return page_response(
        items=agents,
        page=page,
        rows=rows,
        total=count,
        message="获取智能体列表成功"
    )

@router.post("/detail/{uuid}", response_model=BaseResponse[AgentDetailResponse])
def read_agent(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个智能体。"""
    agent_detail = get_agent_detail(session, current_user, uuid=uuid)
    return success_response(data=agent_detail, message="获取智能体详情成功")

@router.post("/create", response_model=BaseResponse[AgentPublic])
def create_agent(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    agent_in: AgentCreate
) -> Any:
    """创建新智能体。"""
    agent_data = agent_in.model_dump()
    agent_data = update_common_fields(
        data=agent_data,
        current_user=current_user,
        is_create=True
    )
    agent_data["model_id"] = 1
    agent = Agent.model_validate(agent_data)
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return success_response(
        data=agent,
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )

@router.post("/update/{uuid}", response_model=BaseResponse[AgentPublic])
def update_agent(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    agent_in: AgentUpdate,
) -> Any:
    """更新智能体信息。"""
    from qiushuiai.schemas.knowledge import KbKnowledge
    from qiushuiai.schemas.tools import Tools
    
    agent = get_agent_by_uuid(session, current_user, uuid)
    if not agent:
        raise ResourceNotFoundException(message="智能体不存在")
    
    # 提取高级保存相关字段
    save_mode = agent_in.save_mode or "basic"
    knowledge_uuids = agent_in.knowledge_uuids
    tool_uuids = agent_in.tool_uuids
    
    # 更新基本信息
    update_dict = agent_in.model_dump(exclude_unset=True, exclude={"save_mode", "knowledge_uuids", "tool_uuids"})
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )
    agent.sqlmodel_update(update_dict)
    session.add(agent)
    
    # 处理高级保存模式
    if save_mode == "advanced":
        # 处理知识库关联
        if knowledge_uuids is not None:
            # 删除现有的知识库关联
            existing_knowledge_relations = session.exec(
                select(AgentKnowledge).where(AgentKnowledge.agent_id == agent.id)
            ).all()
            for relation in existing_knowledge_relations:
                session.delete(relation)
            
            # 添加新的知识库关联
            if knowledge_uuids:
                for knowledge_uuid in knowledge_uuids:
                    # 验证知识库是否存在且属于当前用户租户
                    knowledge = session.exec(
                        select(KbKnowledge).where(
                            KbKnowledge.uuid == knowledge_uuid,
                            KbKnowledge.tenant_id == current_user.tenant_id,
                            KbKnowledge.is_del == False
                        )
                    ).first()
                    
                    if knowledge:
                        agent_knowledge = AgentKnowledge(
                            agent_id=agent.id,
                            knowledge_id=knowledge.id
                        )
                        session.add(agent_knowledge)
        
        # 处理工具关联
        if tool_uuids is not None:
            # 删除现有的工具关联
            existing_tool_relations = session.exec(
                select(AgentTools).where(AgentTools.agent_id == agent.id)
            ).all()
            for relation in existing_tool_relations:
                session.delete(relation)
            
            # 添加新的工具关联
            if tool_uuids:
                for tool_uuid in tool_uuids:
                    # 验证工具是否存在且属于当前用户租户
                    tool = session.exec(
                        select(Tools).where(
                            Tools.uuid == tool_uuid,
                            Tools.tenant_id == current_user.tenant_id
                        )
                    ).first()
                    
                    if tool:
                        agent_tool = AgentTools(
                            agent_id=agent.id,
                            tool_id=tool.id
                        )
                        session.add(agent_tool)
    
    session.commit()
    session.refresh(agent)
    return success_response(data=agent, message=ResponseMessage.UPDATED)

@router.post("/delete/{uuid}", response_model=BaseResponse[None])
def delete_agent(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """删除智能体（软删除）。"""
    agent = get_agent_by_uuid(session, current_user, uuid)
    if not agent:
        raise ResourceNotFoundException(message="智能体不存在")
    delete_data = {"is_del": True}
    delete_data = update_common_fields(
        data=delete_data,
        current_user=current_user,
        is_create=False
    )
    agent.sqlmodel_update(delete_data)
    session.add(agent)
    session.commit()
    return success_response(data=None, message=ResponseMessage.DELETED)

@router.post("/delete-knowledge/{agent_uuid}/{knowledge_uuid}", response_model=BaseResponse[None])
def delete_agent_knowledge(
    session: SessionDep,
    current_user: CurrentUser,
    agent_uuid: uuid_module.UUID,
    knowledge_uuid: uuid_module.UUID
) -> Any:
    """删除智能体关联的单个知识库。"""
    from qiushuiai.schemas.knowledge import KbKnowledge
    
    # 验证智能体是否存在且属于当前用户
    agent = get_agent_by_uuid(session, current_user, agent_uuid)
    if not agent:
        raise ResourceNotFoundException(message="智能体不存在")
    
    # 验证知识库是否存在且属于当前用户租户
    knowledge = session.exec(
        select(KbKnowledge).where(
            KbKnowledge.uuid == knowledge_uuid,
            KbKnowledge.tenant_id == current_user.tenant_id,
            KbKnowledge.is_del == False
        )
    ).first()
    if not knowledge:
        raise ResourceNotFoundException(message="知识库不存在")
    
    # 查找并删除关联关系
    agent_knowledge_relation = session.exec(
        select(AgentKnowledge).where(
            AgentKnowledge.agent_id == agent.id,
            AgentKnowledge.knowledge_id == knowledge.id
        )
    ).first()
    
    if not agent_knowledge_relation:
        raise ResourceNotFoundException(message="智能体与知识库的关联关系不存在")
    
    session.delete(agent_knowledge_relation)
    session.commit()
    
    return success_response(data=None, message="删除智能体知识库关联成功")

@router.post("/delete-tool/{agent_uuid}/{tool_uuid}", response_model=BaseResponse[None])
def delete_agent_tool(
    session: SessionDep,
    current_user: CurrentUser,
    agent_uuid: uuid_module.UUID,
    tool_uuid: uuid_module.UUID
) -> Any:
    """删除智能体关联的单个工具。"""
    from qiushuiai.schemas.tools import Tools
    
    # 验证智能体是否存在且属于当前用户
    agent = get_agent_by_uuid(session, current_user, agent_uuid)
    if not agent:
        raise ResourceNotFoundException(message="智能体不存在")
    
    # 验证工具是否存在且属于当前用户租户
    tool = session.exec(
        select(Tools).where(
            Tools.uuid == tool_uuid,
            Tools.tenant_id == current_user.tenant_id
        )
    ).first()
    if not tool:
        raise ResourceNotFoundException(message="工具不存在")
    
    # 查找并删除关联关系
    agent_tool_relation = session.exec(
        select(AgentTools).where(
            AgentTools.agent_id == agent.id,
            AgentTools.tool_id == tool.id
        )
    ).first()
    
    if not agent_tool_relation:
        raise ResourceNotFoundException(message="智能体与工具的关联关系不存在")
    
    session.delete(agent_tool_relation)
    session.commit()
    
    return success_response(data=None, message="删除智能体工具关联成功") 

@router.post("/save-knowledge/{agent_uuid}", response_model=BaseResponse[None])
def save_agent_knowledge(
    session: SessionDep,
    current_user: CurrentUser,
    agent_uuid: uuid_module.UUID,
    knowledge_uuids: list[uuid_module.UUID] = Body(...)
) -> Any:
    """批量保存智能体与知识库的关联关系。"""
    from qiushuiai.schemas.knowledge import KbKnowledge
    
    # 验证智能体是否存在且属于当前用户
    agent = get_agent_by_uuid(session, current_user, agent_uuid)
    if not agent:
        raise ResourceNotFoundException(message="智能体不存在")
    
    # 删除现有的知识库关联
    existing_knowledge_relations = session.exec(
        select(AgentKnowledge).where(AgentKnowledge.agent_id == agent.id)
    ).all()
    for relation in existing_knowledge_relations:
        session.delete(relation)
    
    # 添加新的知识库关联
    if knowledge_uuids:
        for knowledge_uuid in knowledge_uuids:
            # 验证知识库是否存在且属于当前用户租户
            knowledge = session.exec(
                select(KbKnowledge).where(
                    KbKnowledge.uuid == knowledge_uuid,
                    KbKnowledge.tenant_id == current_user.tenant_id,
                    KbKnowledge.is_del == False
                )
            ).first()
            
            if knowledge:
                agent_knowledge = AgentKnowledge(
                    agent_id=agent.id,
                    knowledge_id=knowledge.id
                )
                session.add(agent_knowledge)
    
    session.commit()
    return success_response(data=None, message="保存智能体知识库关联成功")

import logging

@router.post("/save-tool/{agent_uuid}", response_model=BaseResponse[None])
def save_agent_tool(
    session: SessionDep,
    current_user: CurrentUser,
    agent_uuid: uuid_module.UUID,
    tool_uuids: list[uuid_module.UUID] = Body(...)
) -> Any:
    """批量保存智能体与工具的关联关系。"""
    from qiushuiai.schemas.tools import Tools

    logger = logging.getLogger("qiushuiai.agent_api")

    # 验证智能体是否存在且属于当前用户
    agent = get_agent_by_uuid(session, current_user, agent_uuid)
    if not agent:
        logger.warning(f"保存工具失败：未找到agent_uuid={agent_uuid}，user_id={current_user.id}")
        raise ResourceNotFoundException(message="智能体不存在")

    # 添加新的工具关联
    added_tools = []
    not_found_tools = []
    if tool_uuids:
        for tool_uuid in tool_uuids:
            # 验证工具是否存在且属于当前用户租户
            tool = session.exec(
                select(Tools).where(
                    Tools.uuid == tool_uuid,
                    Tools.tenant_id == current_user.tenant_id
                )
            ).first()

            if tool:
                agent_tool = AgentTools(
                    agent_id=agent.id,
                    tool_id=tool.id
                )
                session.add(agent_tool)
                added_tools.append(str(tool_uuid))
            else:
                not_found_tools.append(str(tool_uuid))

    session.commit()

    # 提交后再次查询确认
    saved_relations = session.exec(
        select(AgentTools).where(AgentTools.agent_id == agent.id)
    ).all()
    saved_tool_ids = [relation.tool_id for relation in saved_relations]
    logger.info(
        f"保存agent_id={agent.id}工具关联，期望添加{len(tool_uuids)}个，实际添加{len(saved_tool_ids)}个，"
        f"成功工具UUIDs={added_tools}，未找到工具UUIDs={not_found_tools}，最终数据库tool_ids={saved_tool_ids}"
    )

    return success_response(data=None, message="保存智能体工具关联成功") 

@router.post("/organization", response_model=BaseResponse[AgentOrganizationResponse])
def get_agent_organization(
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """获取智能体组织架构，包括树形标签和所有智能体列表。"""
    # 获取树形标签数据（使用flag="agent"）
    sys_tags_service = SysTagsService(session)
    tree_data = sys_tags_service.get_tree_by_flag("agent", current_user)
    
    # 获取所有智能体列表
    statement = select(Agent)
    statement = apply_common_filters(
        statement=statement,
        model=Agent,
        current_user=current_user
    )
    statement = build_order_by(
        statement=statement,
        model=Agent,
        order_by="id",
        order_direction="desc"
    )
    agents = session.exec(statement).all()
    
    # 构建响应数据
    organization_data = AgentOrganizationResponse(
        tree_data=tree_data,
        agents=agents
    )
    
    return success_response(
        data=organization_data, 
        message="获取智能体组织架构成功"
    ) 