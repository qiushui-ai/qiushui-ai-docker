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
from qiushuiai.schemas.sys import (
    SysTags,
    SysTagsCreate,
    SysTagsPublic,
    SysTagsUpdate,
)
from qiushuiai.modules.sys.sys_tags_service import SysTagsService


router = APIRouter(prefix="/sys/tags", tags=["sys_tags"])

 
@router.post("/tree", response_model=BaseResponse[list])
def get_sys_tags_tree(
    session: SessionDep, 
    current_user: CurrentUser, 
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取系统标签树形结构。"""
    flag = request_data.get("flag")
    
    if not flag:
        return success_response(
            data=[], 
            message="请提供flag参数",
            code=ResponseCode.BAD_REQUEST
        )
    
    # 使用服务层获取树形结构 
    service = SysTagsService(session)
    tree_data = service.get_tree_by_flag(flag, current_user)
    
    return success_response(
        data=tree_data, 
        message="获取系统标签树形结构成功"
    )


@router.post("/detail/{uuid}", response_model=BaseResponse[SysTagsPublic])
def read_sys_tags(
    session: SessionDep, 
    current_user: CurrentUser, 
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个系统标签。"""
    service = SysTagsService(session)
    tag = service.get_tag_by_uuid(uuid)
    
    return success_response(data=tag, message="获取系统标签详情成功")


@router.post("/create", response_model=BaseResponse[SysTagsPublic])
def create_sys_tags(
    *, 
    session: SessionDep, 
    current_user: CurrentUser, 
    tag_in: SysTagsCreate
) -> Any:
    """创建新系统标签。
    
    自动处理父节点赋值：
    - 如果提供了 puuid，会自动验证父节点存在性
    - 自动计算并设置 pname（父名称路径）
    - 支持创建根节点（不提供 puuid）或子节点（提供 puuid）
    """
    service = SysTagsService(session)
    tag = service.create_tag(tag_in, current_user)
    
    return success_response(
        data=tag, 
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )


@router.post("/update/{uuid}", response_model=BaseResponse[SysTagsPublic])
def update_sys_tags(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    tag_in: SysTagsUpdate,
) -> Any:
    """更新系统标签信息。"""
    service = SysTagsService(session)
    tag = service.update_tag(uuid, tag_in, current_user)
    
    return success_response(data=tag, message=ResponseMessage.UPDATED)


@router.post("/delete/{uuid}", response_model=BaseResponse[None])
def delete_sys_tags(
    session: SessionDep, 
    current_user: CurrentUser, 
    uuid: uuid_module.UUID
) -> Any:
    """删除系统标签及其所有子节点。"""
    service = SysTagsService(session)
    service.delete_tag(uuid)
    
    return success_response(data=None, message=ResponseMessage.DELETED)


@router.post("/page", response_model=BaseResponse[PageResponse[SysTagsPublic]])
def page_sys_tags(
    session: SessionDep, 
    current_user: CurrentUser, 
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取系统标签列表（分页）。"""
    # 提取参数，设置默认值
    page = request_data.get("page", 1)
    rows = request_data.get("rows", 20)
    keyword = request_data.get("keyword")
    flag = request_data.get("flag")  # 根据类别筛选
    
    # 构建基础查询
    statement = select(SysTags)
    
    # 应用通用过滤条件
    statement = apply_common_filters(
        statement=statement,
        model=SysTags,
        current_user=current_user
    )
    
    # 根据类别筛选
    if flag:
        statement = statement.where(SysTags.flag == flag)
    
    # 应用关键词搜索
    statement = apply_keyword_search(
        statement=statement,
        model=SysTags,
        keyword=keyword,
        search_fields=["name", "pname", "remark"]
    )
    
    # 构建计数查询
    count_statement = get_count_query(statement, SysTags)
    count = session.exec(count_statement).one()
    
    # 添加排序 - 优先按sortorder排序，然后按id倒序
    statement = build_order_by(
        statement=statement,
        model=SysTags,
        order_by="sortorder",
        order_direction="asc"
    )
    statement = statement.order_by(SysTags.id.desc())
    
    # 应用分页
    statement, _, _ = apply_pagination(
        statement=statement,
        page=page,
        page_size=rows
    )
    
    # 执行查询
    tags = session.exec(statement).all()
    
    # 使用标准分页响应格式
    return page_response(
        items=tags,
        page=page,
        rows=rows,
        total=count,
        message="获取系统标签列表成功"
    )


@router.post("/list", response_model=BaseResponse[list[SysTagsPublic]])
def list_sys_tags(
    session: SessionDep, 
    current_user: CurrentUser, 
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取系统标签列表（不分页）。"""
    flag = request_data.get("flag")  # 根据类别筛选
    
    # 构建基础查询
    statement = select(SysTags)
    
    # 应用通用过滤条件
    statement = apply_common_filters(
        statement=statement,
        model=SysTags,
        current_user=current_user
    )
    
    # 根据类别筛选
    if flag:
        statement = statement.where(SysTags.flag == flag)
    
    # 添加排序 - 优先按sortorder排序，然后按id倒序
    statement = build_order_by(
        statement=statement,
        model=SysTags,
        order_by="sortorder",
        order_direction="asc"
    )
    statement = statement.order_by(SysTags.id.desc())
    
    # 执行查询
    tags = session.exec(statement).all()
    
    return success_response(data=tags, message="获取系统标签列表成功") 