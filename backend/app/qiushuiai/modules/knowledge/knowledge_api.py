from typing import Any, Annotated
from datetime import datetime
import uuid as uuid_module

from fastapi import APIRouter, Body
from sqlmodel import func, select

from qiushuiai.modules.user.deps import CurrentUser, SessionDep
from qiushuiai.modules.user.deps_unified import CurrentUserUnified
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
from qiushuiai.schemas.knowledge import (
    KbKnowledge,
    KbKnowledgeCreate,
    KbKnowledgePublic,
    KbKnowledgeUpdate,
)


router = APIRouter(prefix="/knowledge", tags=["knowledge"])

 
@router.post("/page", response_model=BaseResponse[PageResponse[KbKnowledgePublic]])
def page_knowledges(
    session: SessionDep,
    current_user: CurrentUser,  # 支持JWT + API Key双重认证
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取知识库列表 - 支持JWT Token和API Key双重认证。"""
    # 提取参数，设置默认值
    page = request_data.get("page", 1)
    rows = request_data.get("rows", 20)
    keyword = request_data.get("keyword")
    # 构建基础查询
    statement = select(KbKnowledge)
    
    # 应用通用过滤条件
    statement = apply_common_filters(
        statement=statement,
        model=KbKnowledge,
        current_user=current_user
    )
    
    # 应用关键词搜索
    statement = apply_keyword_search(
        statement=statement,
        model=KbKnowledge,
        keyword=keyword,
        search_fields=["name", "description", "tags"]
    )
    
    # 构建计数查询
    count_statement = get_count_query(statement, KbKnowledge)
    count = session.exec(count_statement).one()
    
    # 添加排序
    statement = build_order_by(
        statement=statement,
        model=KbKnowledge,
        order_by="id",
        order_direction="desc"
    ) 
    
    # 应用分页
    statement, _, _ = apply_pagination(
        statement=statement,
        page=page,
        page_size=rows
    )
    
    # 执行查询
    knowledges = session.exec(statement).all()
    
    # 使用标准分页响应格式
    return page_response(
        items=knowledges,
        page=page,
        rows=rows,
        total=count,
        message="获取知识库列表成功"
    )


@router.post("/detail/{uuid}", response_model=BaseResponse[KbKnowledgePublic])
def read_knowledge(
    session: SessionDep,
    current_user: CurrentUser,  # 支持JWT + API Key双重认证
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个知识库。"""
    statement = select(KbKnowledge).where(KbKnowledge.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=KbKnowledge,
        current_user=current_user
    )
    knowledge = session.exec(statement).first()
    
    if not knowledge:
        raise ResourceNotFoundException(message="知识库不存在")
    
    return success_response(data=knowledge, message="获取知识库详情成功")


@router.post("/create", response_model=BaseResponse[KbKnowledgePublic])
def create_knowledge(
    *,
    session: SessionDep,
    current_user: CurrentUser,  # 支持JWT + API Key双重认证 
    knowledge_in: KbKnowledgeCreate
) -> Any:
    """创建新知识库。"""
    knowledge_data = knowledge_in.model_dump()
    
    # 使用通用函数更新公共字段
    knowledge_data = update_common_fields(
        data=knowledge_data,
        current_user=current_user,
        is_create=True
    )
    
    knowledge = KbKnowledge.model_validate(knowledge_data)
    session.add(knowledge)
    session.commit()
    session.refresh(knowledge)
    return success_response(
        data=knowledge, 
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )


@router.post("/update/{uuid}", response_model=BaseResponse[KbKnowledgePublic])
def update_knowledge(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    knowledge_in: KbKnowledgeUpdate,
) -> Any:
    """更新知识库信息。"""
    statement = select(KbKnowledge).where(KbKnowledge.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=KbKnowledge,
        current_user=current_user
    )
    knowledge = session.exec(statement).first()
    
    if not knowledge:
        raise ResourceNotFoundException(message="知识库不存在")
    
    update_dict = knowledge_in.model_dump(exclude_unset=True)
    
    # 使用通用函数更新公共字段
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )
    
    knowledge.sqlmodel_update(update_dict)
    session.add(knowledge)
    session.commit()
    session.refresh(knowledge)
    return success_response(data=knowledge, message=ResponseMessage.UPDATED)


@router.post("/delete/{uuid}", response_model=BaseResponse[None])
def delete_knowledge(
    session: SessionDep, 
    current_user: CurrentUser, 
    uuid: uuid_module.UUID
) -> Any:
    """删除知识库（软删除）。"""
    statement = select(KbKnowledge).where(KbKnowledge.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=KbKnowledge,
        current_user=current_user
    )
    knowledge = session.exec(statement).first()
    
    if not knowledge:
        raise ResourceNotFoundException(message="知识库不存在")
    
    # 执行软删除
    delete_data = {"is_del": True}
    delete_data = update_common_fields(
        data=delete_data,
        current_user=current_user,
        is_create=False
    )
    
    knowledge.sqlmodel_update(delete_data)
    session.add(knowledge)
    session.commit()
    return success_response(data=None, message=ResponseMessage.DELETED) 