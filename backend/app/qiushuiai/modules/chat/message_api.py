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
    ChatMessage,
    ChatMessageCreate,
    ChatMessagePublic,
    ChatMessageUpdate,
)

router = APIRouter(prefix="/chat/message", tags=["chat_message"])

@router.post("/page", response_model=BaseResponse[PageResponse[ChatMessagePublic]])
def page_messages(
    session: SessionDep,
    current_user: CurrentUser,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取消息列表。"""
    page = request_data.get("page", 1)
    rows = request_data.get("rows", 20)
    conversation_id = request_data.get("conversation_id")
    keyword = request_data.get("keyword")
    statement = select(ChatMessage)
    if conversation_id:
        statement = statement.where(ChatMessage.conversation_id == conversation_id)
    statement = apply_common_filters(
        statement=statement,
        model=ChatMessage,
        current_user=current_user
    )
    statement = apply_keyword_search(
        statement=statement,
        model=ChatMessage,
        keyword=keyword,
        search_fields=["content"]
    )
    count_statement = get_count_query(statement, ChatMessage)
    count = session.exec(count_statement).one()
    statement = build_order_by(
        statement=statement,
        model=ChatMessage,
        order_by="id",
        order_direction="desc"
    )
    statement, _, _ = apply_pagination(
        statement=statement,
        page=page,
        page_size=rows
    )
    messages = session.exec(statement).all()
    return page_response(
        items=messages,
        page=page,
        rows=rows,
        total=count,
        message="获取消息列表成功"
    )

@router.post("/detail/{uuid}", response_model=BaseResponse[ChatMessagePublic])
def read_message(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单条消息。"""
    statement = select(ChatMessage).where(ChatMessage.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=ChatMessage,
        current_user=current_user
    )
    message = session.exec(statement).first()
    if not message:
        raise ResourceNotFoundException(message="消息不存在")
    return success_response(data=message, message="获取消息详情成功")

@router.post("/create", response_model=BaseResponse[ChatMessagePublic])
def create_message(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    message_in: ChatMessageCreate
) -> Any:
    """创建新消息。"""
    message_data = message_in.model_dump()
    message_data = update_common_fields(
        data=message_data,
        current_user=current_user,
        is_create=True
    )
    message = ChatMessage.model_validate(message_data)
    session.add(message)
    session.commit()
    session.refresh(message)
    return success_response(
        data=message,
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )

@router.post("/update/{uuid}", response_model=BaseResponse[ChatMessagePublic])
def update_message(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    message_in: ChatMessageUpdate,
) -> Any:
    """更新消息内容。"""
    statement = select(ChatMessage).where(ChatMessage.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=ChatMessage,
        current_user=current_user
    )
    message = session.exec(statement).first()
    if not message:
        raise ResourceNotFoundException(message="消息不存在")
    update_dict = message_in.model_dump(exclude_unset=True)
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )
    message.sqlmodel_update(update_dict)
    session.add(message)
    session.commit()
    session.refresh(message)
    return success_response(data=message, message=ResponseMessage.UPDATED)

@router.post("/delete/{uuid}", response_model=BaseResponse[None])
def delete_message(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """删除消息（软删除）。"""
    statement = select(ChatMessage).where(ChatMessage.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=ChatMessage,
        current_user=current_user
    )
    message = session.exec(statement).first()
    if not message:
        raise ResourceNotFoundException(message="消息不存在")
    delete_data = {"metadata": {**(message.metadata or {}), "is_del": True}}
    delete_data = update_common_fields(
        data=delete_data,
        current_user=current_user,
        is_create=False
    )
    message.sqlmodel_update(delete_data)
    session.add(message)
    session.commit()
    return success_response(data=None, message=ResponseMessage.DELETED) 