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
from qiushuiai.schemas.chat import (
    ChatConversation,
    ChatConversationCreate,
    ChatConversationPublic,
    ChatConversationUpdate,
)
from qiushuiai.modules.agent.agent_service import get_agent_detail

router = APIRouter(prefix="/chat/conversation", tags=["chat_conversation"])

@router.post("/page", response_model=BaseResponse[PageResponse[ChatConversationPublic]])
def page_conversations(
    session: SessionDep,
    current_user: CurrentUser,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取对话列表。"""
    print("接收到的请求数据:", request_data)  # 添加日志
    page = request_data.get("page", 1)
    rows = request_data.get("rows", 20)
    keyword = request_data.get("keyword")
    print(f"page: {page}, rows: {rows}, keyword: {keyword}")  # 添加日志
    statement = select(ChatConversation)
    statement = apply_common_filters(
        statement=statement,
        model=ChatConversation,
        current_user=current_user
    )
    statement = apply_keyword_search(
        statement=statement,
        model=ChatConversation,
        keyword=keyword,
        search_fields=["title", "summary"]
    )
    count_statement = get_count_query(statement, ChatConversation)
    count = session.exec(count_statement).one()
    statement = build_order_by(
        statement=statement,
        model=ChatConversation,
        order_by="id",
        order_direction="desc"
    )
    statement, _, _ = apply_pagination(
        statement=statement,
        page=page,
        page_size=rows
    )
    conversations = session.exec(statement).all()
    return page_response(
        items=conversations,
        page=page,
        rows=rows,
        total=count,
        message="获取对话列表成功"
    )

@router.post("/detail/{uuid}", response_model=BaseResponse[ChatConversationPublic])
def read_conversation(
    session: SessionDep,
    current_user: CurrentUser, 
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个对话。"""
    statement = select(ChatConversation).where(ChatConversation.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=ChatConversation,
        current_user=current_user
    )
    
    conversation = session.exec(statement).first()
   
    if not conversation:
        return success_response(data=None, message="对话不存在")
    
    # 创建响应对象，包含智能体信息
    response_data = ChatConversationPublic.model_validate(conversation)
    
    # 只有当 agent_id 不为 None 时才获取智能体详情
    if conversation.agent_uuid is not None:
        try:
            agent = get_agent_detail(session, current_user, uuid=conversation.agent_uuid)
            response_data.agent = agent.model_dump() if agent else None
        except (ValueError, ResourceNotFoundException):
            # 如果智能体不存在或参数错误，设置为 None
            response_data.agent = None
    else:
        response_data.agent = None
    
    return success_response(data=response_data, message="获取对话详情成功")

@router.post("/create", response_model=BaseResponse[ChatConversationPublic])
def create_conversation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    conversation_in: ChatConversationCreate
) -> Any:
    """创建新对话。"""
    conversation_data = conversation_in.model_dump(exclude_unset=True)
    conversation_data["user_id"] = current_user.id
    conversation_data["tenant_id"] = current_user.tenant_id
    conversation_data["message_count"] = 0
    conversation_data["total_tokens"] =0

    # 如果前端传了uuid，使用前端的；否则由数据库自动生成
    # 使用 exclude_unset=True 确保只传递前端实际提供的字段
    
    conversation_data = update_common_fields(
        data=conversation_data,
        current_user=current_user,
        is_create=True
    )
    conversation = ChatConversation.model_validate(conversation_data)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return success_response(
        data=conversation,
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )

@router.post("/update/{uuid}", response_model=BaseResponse[ChatConversationPublic])
def update_conversation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    conversation_in: ChatConversationUpdate,
) -> Any:
    """更新对话信息。"""
    statement = select(ChatConversation).where(ChatConversation.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=ChatConversation,
        current_user=current_user
    )
    conversation = session.exec(statement).first()
    if not conversation:
        raise ResourceNotFoundException(message="对话不存在")
    update_dict = conversation_in.model_dump(exclude_unset=True)
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )
    conversation.sqlmodel_update(update_dict)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return success_response(data=conversation, message=ResponseMessage.UPDATED)

@router.post("/delete/{uuid}", response_model=BaseResponse[None])
def delete_conversation(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """删除对话（物理删除）。"""
    statement = select(ChatConversation).where(ChatConversation.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=ChatConversation,
        current_user=current_user
    )
    conversation = session.exec(statement).first()
    if not conversation:
        raise ResourceNotFoundException(message="对话不存在")
    
    session.delete(conversation)
    session.commit()
    return success_response(data=None, message=ResponseMessage.DELETED)

@router.post("/batch_delete", response_model=BaseResponse[None])
def batch_delete_conversations(
    session: SessionDep,
    current_user: CurrentUser,
    uuids: list[uuid_module.UUID] = Body(...)
) -> Any:
    """批量删除对话（物理删除）。"""
    if not uuids:
        return success_response(data=None, message="没有需要删除的对话")

    statement = select(ChatConversation).where(ChatConversation.uuid.in_(uuids))
    statement = apply_common_filters(
        statement=statement,
        model=ChatConversation,
        current_user=current_user
    )
    conversations = session.exec(statement).all()

    if not conversations:
        raise ResourceNotFoundException(message="没有找到可删除的对话")

    for conversation in conversations:
        session.delete(conversation)

    session.commit()
    return success_response(
        data=None, 
        message=f"成功删除 {len(conversations)} 条对话"
    ) 