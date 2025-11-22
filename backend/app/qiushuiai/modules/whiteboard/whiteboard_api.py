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
    Whiteboard,
    WhiteboardCreate,
    WhiteboardPublic,
    WhiteboardUpdate,
)


router = APIRouter(prefix="/whiteboard", tags=["whiteboard"])


@router.post("/page", response_model=BaseResponse[PageResponse[WhiteboardPublic]])
def page_whiteboard(
    session: SessionDep, 
    current_user: CurrentUser, 
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取白板列表。"""
    # 提取参数，设置默认值
    page = request_data.get("page", 1)
    rows = request_data.get("rows", 20)
    keyword = request_data.get("keyword")
    
    # 构建基础查询
    statement = select(Whiteboard)
    
    # 应用通用过滤条件
    statement = apply_common_filters(
        statement=statement,
        model=Whiteboard,
        current_user=current_user
    )
    
    # 应用关键词搜索
    statement = apply_keyword_search(
        statement=statement,
        model=Whiteboard,
        keyword=keyword,
        search_fields=["title", "description"]
    )
    
    # 构建计数查询
    count_statement = get_count_query(statement, Whiteboard)
    count = session.exec(count_statement).one()
    
    # 添加排序
    statement = build_order_by(
        statement=statement,
        model=Whiteboard,
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
    whiteboards = session.exec(statement).all()
    
    # 使用标准分页响应格式
    return page_response(
        items=whiteboards,
        page=page,
        rows=rows,
        total=count,
        message="获取白板列表成功"
    )


@router.post("/detail/{uuid}", response_model=BaseResponse[WhiteboardPublic])
def read_whiteboard(
    session: SessionDep, 
    current_user: CurrentUser, 
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个白板。"""
    statement = select(Whiteboard).where(Whiteboard.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=Whiteboard,
        current_user=current_user
    )
    whiteboard = session.exec(statement).first()
    
    if not whiteboard:
        raise ResourceNotFoundException(message="白板不存在")
    
    return success_response(data=whiteboard, message="获取白板详情成功")


@router.post("/create", response_model=BaseResponse[WhiteboardPublic])
def create_whiteboard(
    *, 
    session: SessionDep, 
    current_user: CurrentUser, 
    whiteboard_in: WhiteboardCreate
) -> Any:
    """创建新白板。"""
    whiteboard_data = whiteboard_in.model_dump()
    
    # 使用通用函数更新公共字段
    whiteboard_data = update_common_fields(
        data=whiteboard_data,
        current_user=current_user,
        is_create=True
    )
    
    whiteboard = Whiteboard.model_validate(whiteboard_data)
    session.add(whiteboard)
    session.commit()
    session.refresh(whiteboard)
    return success_response(
        data=whiteboard, 
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )


@router.post("/update/{uuid}", response_model=BaseResponse[WhiteboardPublic])
def update_whiteboard(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    whiteboard_in: WhiteboardUpdate,
) -> Any:
    """更新白板信息。"""
    statement = select(Whiteboard).where(Whiteboard.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=Whiteboard,
        current_user=current_user
    )
    whiteboard = session.exec(statement).first()
    
    if not whiteboard:
        raise ResourceNotFoundException(message="白板不存在")
    
    update_dict = whiteboard_in.model_dump(exclude_unset=True)
    
    # 使用通用函数更新公共字段
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )
    
    whiteboard.sqlmodel_update(update_dict)
    session.add(whiteboard)
    session.commit()
    session.refresh(whiteboard)
    return success_response(data=whiteboard, message=ResponseMessage.UPDATED)


@router.post("/delete/{uuid}", response_model=BaseResponse[None])
def delete_whiteboard(
    session: SessionDep, 
    current_user: CurrentUser, 
    uuid: uuid_module.UUID
) -> Any:
    """删除白板（软删除）。"""
    statement = select(Whiteboard).where(Whiteboard.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=Whiteboard,
        current_user=current_user
    )
    whiteboard = session.exec(statement).first()
    
    if not whiteboard:
        raise ResourceNotFoundException(message="白板不存在")
    
    session.delete(whiteboard)
    session.commit()
    return success_response(data=None, message=ResponseMessage.DELETED)
