from typing import Any, Annotated
from datetime import datetime
import uuid as uuid_module

from fastapi import APIRouter, Body
from sqlmodel import func, select

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
from qiushuiai.schemas.whiteboard import (
    WhiteboardNote,
    WhiteboardNoteCreate,
    WhiteboardNotePublic,
    WhiteboardNoteUpdate,
)


router = APIRouter(prefix="/whiteboard-note", tags=["whiteboard-note"])


@router.post("/page", response_model=BaseResponse[PageResponse[WhiteboardNotePublic]])
def page_whiteboard_note(
    session: SessionDep, 
    current_user: CurrentUser, 
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取白板笔记关联列表。"""
    # 提取参数，设置默认值
    page = request_data.get("page", 1)
    rows = request_data.get("rows", 20)
    keyword = request_data.get("keyword")
    whiteboard_uuid = request_data.get("whiteboard_uuid")
    
    # 构建基础查询
    statement = select(WhiteboardNote)
    
    # 应用通用过滤条件
    statement = apply_common_filters(
        statement=statement,
        model=WhiteboardNote,
        current_user=current_user
    )
    
    # 如果指定了白板UUID，添加过滤条件
    if whiteboard_uuid:
        statement = statement.where(WhiteboardNote.whiteboard_uuid == whiteboard_uuid)
    
    # 应用关键词搜索
    statement = apply_keyword_search(
        statement=statement,
        model=WhiteboardNote,
        keyword=keyword,
        search_fields=["shape_id", "shape_type"]
    )
    
    # 构建计数查询
    count_statement = get_count_query(statement, WhiteboardNote)
    count = session.exec(count_statement).one()
    
    # 添加排序
    statement = build_order_by(
        statement=statement,
        model=WhiteboardNote,
        order_by="z_index",
        order_direction="asc"
    ) 
    
    # 应用分页
    statement, _, _ = apply_pagination(
        statement=statement,
        page=page,
        page_size=rows
    )
    
    # 执行查询
    whiteboard_notes = session.exec(statement).all()
    
    # 使用标准分页响应格式
    return page_response(
        items=whiteboard_notes,
        page=page,
        rows=rows,
        total=count,
        message="获取白板笔记关联列表成功"
    )


@router.post("/detail/{uuid}", response_model=BaseResponse[WhiteboardNotePublic])
def read_whiteboard_note(
    session: SessionDep, 
    current_user: CurrentUser, 
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个白板笔记关联。"""
    statement = select(WhiteboardNote).where(WhiteboardNote.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=WhiteboardNote,
        current_user=current_user
    )
    whiteboard_note = session.exec(statement).first()
    
    if not whiteboard_note:
        raise ResourceNotFoundException(message="白板笔记关联不存在")
    
    return success_response(data=whiteboard_note, message="获取白板笔记关联详情成功")


@router.post("/create", response_model=BaseResponse[WhiteboardNotePublic])
def create_whiteboard_note(
    *, 
    session: SessionDep, 
    current_user: CurrentUser, 
    whiteboard_note_in: WhiteboardNoteCreate
) -> Any:
    """创建新白板笔记关联。"""
    whiteboard_note_data = whiteboard_note_in.model_dump()
    
    # 使用通用函数更新公共字段
    whiteboard_note_data = update_common_fields(
        data=whiteboard_note_data,
        current_user=current_user,
        is_create=True
    )
    
    whiteboard_note = WhiteboardNote.model_validate(whiteboard_note_data)
    session.add(whiteboard_note)
    session.commit()
    session.refresh(whiteboard_note)
    return success_response(
        data=whiteboard_note, 
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )


@router.post("/update/{uuid}", response_model=BaseResponse[WhiteboardNotePublic])
def update_whiteboard_note(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    whiteboard_note_in: WhiteboardNoteUpdate,
) -> Any:
    """更新白板笔记关联信息。"""
    statement = select(WhiteboardNote).where(WhiteboardNote.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=WhiteboardNote,
        current_user=current_user
    )
    whiteboard_note = session.exec(statement).first()
    
    if not whiteboard_note:
        raise ResourceNotFoundException(message="白板笔记关联不存在")
    
    update_dict = whiteboard_note_in.model_dump(exclude_unset=True)
    
    # 使用通用函数更新公共字段
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )
    
    whiteboard_note.sqlmodel_update(update_dict)
    session.add(whiteboard_note)
    session.commit()
    session.refresh(whiteboard_note)
    return success_response(data=whiteboard_note, message=ResponseMessage.UPDATED)


@router.post("/delete/{uuid}", response_model=BaseResponse[None])
def delete_whiteboard_note(
    session: SessionDep, 
    current_user: CurrentUser, 
    uuid: uuid_module.UUID
) -> Any:
    """删除白板笔记关联（软删除）。"""
    statement = select(WhiteboardNote).where(WhiteboardNote.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=WhiteboardNote,
        current_user=current_user
    )
    whiteboard_note = session.exec(statement).first()
    
    if not whiteboard_note:
        raise ResourceNotFoundException(message="白板笔记关联不存在")
    
    session.delete(whiteboard_note)
    session.commit()
    return success_response(data=None, message=ResponseMessage.DELETED)


@router.post("/batch-create", response_model=BaseResponse[list[WhiteboardNotePublic]])
def batch_create_whiteboard_note(
    *, 
    session: SessionDep, 
    current_user: CurrentUser, 
    whiteboard_notes_in: list[WhiteboardNoteCreate]
) -> Any:
    """批量创建白板笔记关联。"""
    whiteboard_notes = []
    
    for whiteboard_note_in in whiteboard_notes_in:
        whiteboard_note_data = whiteboard_note_in.model_dump()
        
        # 使用通用函数更新公共字段
        whiteboard_note_data = update_common_fields(
            data=whiteboard_note_data,
            current_user=current_user,
            is_create=True
        )
        
        whiteboard_note = WhiteboardNote.model_validate(whiteboard_note_data)
        whiteboard_notes.append(whiteboard_note)
    
    session.add_all(whiteboard_notes)
    session.commit()
    
    # 刷新所有对象
    for whiteboard_note in whiteboard_notes:
        session.refresh(whiteboard_note)
    
    return success_response(
        data=whiteboard_notes, 
        message="批量创建白板笔记关联成功",
        code=ResponseCode.CREATED
    )


@router.post("/batch-update", response_model=BaseResponse[list[WhiteboardNotePublic]])
def batch_update_whiteboard_note(
    *, 
    session: SessionDep, 
    current_user: CurrentUser, 
    updates: list[dict]
) -> Any:
    """批量更新白板笔记关联。"""
    updated_notes = []
    
    for update_data in updates:
        uuid = update_data.get("uuid")
        if not uuid:
            continue
            
        statement = select(WhiteboardNote).where(WhiteboardNote.uuid == uuid)
        statement = apply_common_filters(
            statement=statement,
            model=WhiteboardNote,
            current_user=current_user
        )
        whiteboard_note = session.exec(statement).first()
        
        if not whiteboard_note:
            continue
        
        # 移除uuid字段，只保留要更新的字段
        update_dict = {k: v for k, v in update_data.items() if k != "uuid"}
        
        # 使用通用函数更新公共字段
        update_dict = update_common_fields(
            data=update_dict,
            current_user=current_user,
            is_create=False
        )
        
        whiteboard_note.sqlmodel_update(update_dict)
        session.add(whiteboard_note)
        updated_notes.append(whiteboard_note)
    
    session.commit()
    
    # 刷新所有对象
    for whiteboard_note in updated_notes:
        session.refresh(whiteboard_note)
    
    return success_response(data=updated_notes, message="批量更新白板笔记关联成功")
