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
from qiushuiai.schemas.prompts import (
    PromptsLib,
    PromptsLibCreate,
    PromptsLibPublic,
    PromptsLibUpdate,
)


router = APIRouter(prefix="/prompts", tags=["prompts"])

 
@router.post("/page", response_model=BaseResponse[PageResponse[PromptsLibPublic]])
def page_prompts(
    session: SessionDep, 
    current_user: CurrentUser, 
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取提示词库列表。"""
    # 提取参数，设置默认值
    page = request_data.get("page", 1)
    rows = request_data.get("rows", 20)
    keyword = request_data.get("keyword")
    # 构建基础查询
    statement = select(PromptsLib)
    
    # 应用通用过滤条件
    statement = apply_common_filters(
        statement=statement,
        model=PromptsLib,
        current_user=current_user
    )
    
    # 应用关键词搜索
    statement = apply_keyword_search(
        statement=statement,
        model=PromptsLib,
        keyword=keyword,
        search_fields=["title", "prompts", "tags"]
    )
    
    # 构建计数查询
    count_statement = get_count_query(statement, PromptsLib)
    count = session.exec(count_statement).one()
    
    # 添加排序
    statement = build_order_by(
        statement=statement,
        model=PromptsLib,
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
    prompts = session.exec(statement).all()
    
    # 使用标准分页响应格式
    return page_response(
        items=prompts,
        page=page,
        rows=rows,
        total=count,
        message="获取提示词库列表成功"
    )


@router.post("/detail/{uuid}", response_model=BaseResponse[PromptsLibPublic])
def read_prompts(
    session: SessionDep, 
    current_user: CurrentUser, 
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个提示词库。"""
    statement = select(PromptsLib).where(PromptsLib.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=PromptsLib,
        current_user=current_user
    )
    prompts = session.exec(statement).first()
    
    if not prompts:
        raise ResourceNotFoundException(message="提示词库不存在")
    
    return success_response(data=prompts, message="获取提示词库详情成功")


@router.post("/create", response_model=BaseResponse[PromptsLibPublic])
def create_prompts(
    *, 
    session: SessionDep, 
    current_user: CurrentUser, 
    prompts_in: PromptsLibCreate
) -> Any:
    """创建新提示词库。"""
    prompts_data = prompts_in.model_dump()
    
    # 使用通用函数更新公共字段
    prompts_data = update_common_fields(
        data=prompts_data,
        current_user=current_user,
        is_create=True
    )
    
    prompts = PromptsLib.model_validate(prompts_data)
    session.add(prompts)
    session.commit()
    session.refresh(prompts)
    return success_response(
        data=prompts, 
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )


@router.post("/update/{uuid}", response_model=BaseResponse[PromptsLibPublic])
def update_prompts(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    prompts_in: PromptsLibUpdate,
) -> Any:
    """更新提示词库信息。"""
    statement = select(PromptsLib).where(PromptsLib.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=PromptsLib,
        current_user=current_user
    )
    prompts = session.exec(statement).first()
    
    if not prompts:
        raise ResourceNotFoundException(message="提示词库不存在")
    
    update_dict = prompts_in.model_dump(exclude_unset=True)
    
    # 使用通用函数更新公共字段
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )
    
    prompts.sqlmodel_update(update_dict)
    session.add(prompts)
    session.commit()
    session.refresh(prompts)
    return success_response(data=prompts, message=ResponseMessage.UPDATED)


@router.post("/delete/{uuid}", response_model=BaseResponse[None])
def delete_prompts(
    session: SessionDep, 
    current_user: CurrentUser, 
    uuid: uuid_module.UUID
) -> Any:
    """删除提示词库（软删除）。"""
    statement = select(PromptsLib).where(PromptsLib.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=PromptsLib,
        current_user=current_user
    )
    prompts = session.exec(statement).first()
    
    if not prompts:
        raise ResourceNotFoundException(message="提示词库不存在")
    
    session.delete(prompts)
    session.commit()
    return success_response(data=None, message=ResponseMessage.DELETED) 