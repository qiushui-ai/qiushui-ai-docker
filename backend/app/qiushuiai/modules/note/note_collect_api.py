from typing import Any, Annotated
from datetime import datetime
import uuid as uuid_module
import json

from fastapi import APIRouter, Body, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import func, select
from sqlalchemy import text
from qiushuiai.modules.user.deps_unified import CurrentUserUnified
from qiushuiai.modules.user.deps import CurrentUser, SessionDep
from qiushuiai.core.security import security, verify_api_key
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
from qiushuiai.core.exceptions import ResourceNotFoundException, ValidationException
from qiushuiai.schemas.note import (
    NoteCollect,
    NoteCollectCreate,
    NoteCollectPublic,
    NoteCollectUpdate,
)


router = APIRouter(prefix="/note/collect", tags=["note_collect"])


@router.post("/page", response_model=BaseResponse[PageResponse[NoteCollectPublic]])
def page_note_collect(
    session: SessionDep,
    current_user: CurrentUser,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取收藏笔记列表（分页）。

    支持筛选条件：
    - keyword: 关键词搜索（标题、描述、内容、作者）
    - platform: 平台筛选
    - content_type: 内容类型筛选
    - status: 状态筛选
    - categories: 分类筛选（数组，检查category字段的所有子数组）
    """
    # 提取参数，设置默认值
    page = request_data.get("page", 1)
    rows = request_data.get("rows", 20)
    keyword = request_data.get("keyword")
    platform = request_data.get("platform")
    content_type = request_data.get("content_type")
    status = request_data.get("status")
    categories = request_data.get("categories", [])

    # 构建基础查询
    statement = select(NoteCollect)

    # 应用通用过滤条件
    statement = apply_common_filters(
        statement=statement,
        model=NoteCollect,
        current_user=current_user
    )

    # 根据平台筛选
    if platform:
        statement = statement.where(NoteCollect.platform == platform)

    # 根据内容类型筛选
    if content_type:
        statement = statement.where(NoteCollect.content_type == content_type)

    # 根据状态筛选
    if status is not None:
        statement = statement.where(NoteCollect.status == status)

    # 根据分类筛选
    if categories and isinstance(categories, list) and len(categories) > 0:
        # 构建查询条件：检查 category 字段的任意子数组是否包含指定的 categories
        # category 的结构可能是 {"main": ["qushi", "shicao"], "sub": ["xxx"]}
        # 需要检查所有这些子数组中是否包含传入的 categories 中的任意一个
        
        # 构建查询：使用 EXISTS 子查询检查 category 对象的任意值（数组）是否包含指定的 category
        # 使用 jsonb_each 展开 category 对象，检查每个值（数组）是否包含指定的 category
        # 同时需要检查 category 字段不为 NULL
        conditions = []
        for category in categories:
            category_json = json.dumps([category])
            conditions.append(
                f"(category IS NOT NULL AND EXISTS (SELECT 1 FROM jsonb_each(category) AS kv WHERE kv.value @> '{category_json}'::jsonb))"
            )
        
        if conditions:
            # 使用 OR 连接所有条件
            category_condition = " OR ".join(conditions)
            statement = statement.where(text(category_condition))

    # 应用关键词搜索
    statement = apply_keyword_search(
        statement=statement,
        model=NoteCollect,
        keyword=keyword,
        search_fields=["title", "description", "cn_content", "author_name"]
    )

    # 构建计数查询
    count_statement = get_count_query(statement, NoteCollect)
    count = session.exec(count_statement).one()

    # 添加排序 - 默认按发布时间倒序
    statement = build_order_by(
        statement=statement,
        model=NoteCollect,
        order_by="publish_time",
        order_direction="desc"
    )

    # 应用分页
    statement, _, _ = apply_pagination(
        statement=statement,
        page=page,
        page_size=rows
    )

    # 执行查询
    collects = session.exec(statement).all()

    # 使用标准分页响应格式
    return page_response(
        items=collects,
        page=page,
        rows=rows,
        total=count,
        message="获取收藏笔记列表成功"
    )


@router.post("/detail/{uuid}", response_model=BaseResponse[NoteCollectPublic])
def read_note_collect(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个收藏笔记。"""
    statement = select(NoteCollect).where(NoteCollect.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=NoteCollect,
        current_user=current_user
    )
    collect = session.exec(statement).first()

    if not collect:
        raise ResourceNotFoundException(message="收藏笔记不存在")

    return success_response(data=collect, message="获取收藏笔记详情成功")


@router.post("/detail_by_content_id/{content_id}", response_model=BaseResponse[NoteCollectPublic])
def read_note_collect_by_content_id(
    session: SessionDep,
    current_user: CurrentUser,
    content_id: str
) -> Any:
    """根据content_id获取单个收藏笔记。"""
    statement = select(NoteCollect).where(NoteCollect.content_id == content_id)
    statement = apply_common_filters(
        statement=statement,
        model=NoteCollect,
        current_user=current_user
    )
    collect = session.exec(statement).first()

    if not collect:
        raise ResourceNotFoundException(message="收藏笔记不存在")

    return success_response(data=collect, message="获取收藏笔记详情成功")


@router.post("/create", response_model=BaseResponse[NoteCollectPublic])
def create_note_collect(
    *,
    session: SessionDep,
    current_user: CurrentUserUnified,
    collect_in: NoteCollectCreate
) -> Any:
    """创建新收藏笔记。

    注意：content_id 必须唯一。
    """
    # 检查 content_id 是否已存在
    existing = session.exec(
        select(NoteCollect).where(NoteCollect.content_id == collect_in.content_id)
    ).first()

    if existing:
        raise ValidationException(message=f"content_id '{collect_in.content_id}' 已存在")

    collect_data = collect_in.model_dump()

    # 使用通用函数更新公共字段
    collect_data = update_common_fields(
        data=collect_data,
        current_user=current_user,
        is_create=True
    )

    collect = NoteCollect.model_validate(collect_data)
    session.add(collect)
    session.commit()
    session.refresh(collect)
    return success_response(
        data=collect,
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )


@router.post("/update/{uuid}", response_model=BaseResponse[NoteCollectPublic])
def update_note_collect(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    collect_in: NoteCollectUpdate,
) -> Any:
    """更新收藏笔记信息。"""
    statement = select(NoteCollect).where(NoteCollect.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=NoteCollect,
        current_user=current_user
    )
    collect = session.exec(statement).first()

    if not collect:
        raise ResourceNotFoundException(message="收藏笔记不存在")

    update_dict = collect_in.model_dump(exclude_unset=True)

    # 如果更新 content_id，检查是否已存在
    if "content_id" in update_dict and update_dict["content_id"] != collect.content_id:
        existing = session.exec(
            select(NoteCollect).where(NoteCollect.content_id == update_dict["content_id"])
        ).first()
        if existing:
            raise ValidationException(message=f"content_id '{update_dict['content_id']}' 已存在")

    # 使用通用函数更新公共字段
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )

    collect.sqlmodel_update(update_dict)
    session.add(collect)
    session.commit()
    session.refresh(collect)
    return success_response(data=collect, message=ResponseMessage.UPDATED)


@router.post("/delete/{uuid}", response_model=BaseResponse[None])
def delete_note_collect(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """删除收藏笔记。"""
    statement = select(NoteCollect).where(NoteCollect.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=NoteCollect,
        current_user=current_user
    )
    collect = session.exec(statement).first()

    if not collect:
        raise ResourceNotFoundException(message="收藏笔记不存在")

    session.delete(collect)
    session.commit()
    return success_response(data=None, message=ResponseMessage.DELETED)


@router.post("/list", response_model=BaseResponse[list[NoteCollectPublic]])
def list_note_collect(
    session: SessionDep,
    current_user: CurrentUser,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取收藏笔记列表（不分页）。

    支持筛选条件：
    - platform: 平台筛选
    - content_type: 内容类型筛选
    - status: 状态筛选
    """
    platform = request_data.get("platform")
    content_type = request_data.get("content_type")
    status = request_data.get("status")

    # 构建基础查询
    statement = select(NoteCollect)

    # 应用通用过滤条件
    statement = apply_common_filters(
        statement=statement,
        model=NoteCollect,
        current_user=current_user
    )

    # 根据平台筛选
    if platform:
        statement = statement.where(NoteCollect.platform == platform)

    # 根据内容类型筛选
    if content_type:
        statement = statement.where(NoteCollect.content_type == content_type)

    # 根据状态筛选
    if status is not None:
        statement = statement.where(NoteCollect.status == status)

    # 添加排序 - 默认按发布时间倒序
    statement = build_order_by(
        statement=statement,
        model=NoteCollect,
        order_by="publish_time",
        order_direction="desc"
    )

    # 执行查询
    collects = session.exec(statement).all()

    return success_response(data=collects, message="获取收藏笔记列表成功")


@router.post("/update_stats/{uuid}", response_model=BaseResponse[NoteCollectPublic])
def update_note_collect_stats(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    stats_data: Annotated[dict, Body(...)]
) -> Any:
    """更新收藏笔记的统计数据。

    可更新字段：view_count, like_count, comment_count, share_count, collect_count
    """
    statement = select(NoteCollect).where(NoteCollect.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=NoteCollect,
        current_user=current_user
    )
    collect = session.exec(statement).first()

    if not collect:
        raise ResourceNotFoundException(message="收藏笔记不存在")

    # 只允许更新统计字段
    allowed_fields = ["view_count", "like_count", "comment_count", "share_count", "collect_count"]
    update_dict = {k: v for k, v in stats_data.items() if k in allowed_fields}

    if update_dict:
        collect.sqlmodel_update(update_dict)
        session.add(collect)
        session.commit()
        session.refresh(collect)

    return success_response(data=collect, message="更新统计数据成功")
