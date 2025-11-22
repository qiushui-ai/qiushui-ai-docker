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
    NoteCollectContent,
    NoteCollectContentCreate,
    NoteCollectContentUpdate,
    NoteCollectCreateWithContent,
    NoteCollectUpdateWithContent,
    NoteCollectWithContent,
)


router = APIRouter(prefix="/note/collect", tags=["note_collect"])


def _get_collect_with_content(
    session: SessionDep,
    collect_uuid: uuid_module.UUID,
    current_user: CurrentUser
) -> NoteCollectWithContent | None:
    """获取包含内容的收藏笔记"""
    # 查询主表
    collect_statement = select(NoteCollect).where(NoteCollect.uuid == collect_uuid)
    collect_statement = apply_common_filters(
        statement=collect_statement,
        model=NoteCollect,
        current_user=current_user
    )
    collect = session.exec(collect_statement).first()

    if not collect:
        return None

    # 查询内容表
    content_statement = select(NoteCollectContent).where(
        NoteCollectContent.collect_uuid == collect_uuid
    )
    content = session.exec(content_statement).first()

    # 合并数据
    collect_dict = collect.model_dump()
    if content:
        collect_dict.update({
            "cn_content": content.cn_content,
            "en_content": content.en_content,
            "extdata": content.extdata
        })
    else:
        collect_dict.update({
            "cn_content": None,
            "en_content": None,
            "extdata": None
        })

    return NoteCollectWithContent.model_validate(collect_dict)


def _create_collect_with_content(
    session: SessionDep,
    current_user: CurrentUserUnified,
    collect_data: NoteCollectCreateWithContent
) -> NoteCollectWithContent:
    """创建包含内容的收藏笔记"""
    # 提取主表数据
    main_data = {k: v for k, v in collect_data.model_dump().items()
                 if k not in ["cn_content", "en_content", "extdata"]}

    # 使用通用函数更新公共字段
    main_data = update_common_fields(
        data=main_data,
        current_user=current_user,
        is_create=True
    )

    # 创建主表记录
    collect = NoteCollect.model_validate(main_data)
    session.add(collect)
    session.flush()  # 获取UUID

    # 创建内容表记录（如果有内容）
    if (collect_data.cn_content or collect_data.en_content or collect_data.extdata):
        content_data = {
            "collect_uuid": collect.uuid,
            "cn_content": collect_data.cn_content,
            "en_content": collect_data.en_content,
            "extdata": collect_data.extdata,
            "tenant_id": collect.tenant_id,
            "created_by": collect.created_by,
            "updated_by": collect.updated_by,
            "created_at": collect.created_at,
            "updated_at": collect.updated_at,
        }
        content = NoteCollectContent.model_validate(content_data)
        session.add(content)

    session.commit()
    session.refresh(collect)

    # 返回合并后的数据
    return _get_collect_with_content(session, collect.uuid, current_user)


def _update_collect_with_content(
    session: SessionDep,
    current_user: CurrentUser,
    collect: NoteCollect,
    update_data: NoteCollectUpdateWithContent
) -> NoteCollectWithContent:
    """更新包含内容的收藏笔记"""
    update_dict = update_data.model_dump(exclude_unset=True)

    # 分离主表和内容表数据
    main_fields = {k: v for k, v in update_dict.items()
                   if k not in ["cn_content", "en_content", "extdata"]}
    content_fields = {k: v for k, v in update_dict.items()
                      if k in ["cn_content", "en_content", "extdata"]}

    # 更新主表
    if main_fields:
        main_fields = update_common_fields(
            data=main_fields,
            current_user=current_user,
            is_create=False
        )
        collect.sqlmodel_update(main_fields)
        session.add(collect)

    # 更新内容表
    if content_fields:
        # 查找现有内容
        content = session.exec(
            select(NoteCollectContent).where(
                NoteCollectContent.collect_uuid == collect.uuid
            )
        ).first()

        if content:
            # 更新现有内容
            content_fields["updated_at"] = datetime.now()
            content_fields["updated_by"] = current_user.id
            content.sqlmodel_update(content_fields)
            session.add(content)
        else:
            # 创建新内容
            content_data = {
                "collect_uuid": collect.uuid,
                "cn_content": content_fields.get("cn_content"),
                "en_content": content_fields.get("en_content"),
                "extdata": content_fields.get("extdata"),
                "tenant_id": collect.tenant_id,
                "created_by": current_user.id,
                "updated_by": current_user.id,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
            content = NoteCollectContent.model_validate(content_data)
            session.add(content)

    session.commit()
    session.refresh(collect)

    # 返回合并后的数据
    return _get_collect_with_content(session, collect.uuid, current_user)


@router.post("/page", response_model=BaseResponse[PageResponse[NoteCollectWithContent]])
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

    # 应用关键词搜索（包含主表和内容表）
    if keyword:
        from sqlalchemy import or_

        # 构建主表搜索条件
        main_conditions = []
        if hasattr(NoteCollect, 'title'):
            main_conditions.append(NoteCollect.title.ilike(f"%{keyword}%"))
        if hasattr(NoteCollect, 'description'):
            main_conditions.append(NoteCollect.description.ilike(f"%{keyword}%"))
        if hasattr(NoteCollect, 'author_name'):
            main_conditions.append(NoteCollect.author_name.ilike(f"%{keyword}%"))

        # 构建内容表搜索条件
        content_uuids = select(NoteCollectContent.collect_uuid).where(
            or_(
                NoteCollectContent.cn_content.ilike(f"%{keyword}%"),
                NoteCollectContent.en_content.ilike(f"%{keyword}%")
            )
        )

        # 合并搜索条件：主表条件 OR 存在于内容表
        all_conditions = main_conditions + [NoteCollect.uuid.in_(content_uuids)]
        if all_conditions:
            statement = statement.where(or_(*all_conditions))

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

    # 批量获取包含内容的数据
    collects_with_content = _get_collects_with_content(session, collects)

    # 使用标准分页响应格式
    return page_response(
        items=collects_with_content,
        page=page,
        rows=rows,
        total=count,
        message="获取收藏笔记列表成功"
    )


@router.post("/detail/{uuid}", response_model=BaseResponse[NoteCollectWithContent])
def read_note_collect(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个收藏笔记。"""
    collect_with_content = _get_collect_with_content(session, uuid, current_user)

    if not collect_with_content:
        raise ResourceNotFoundException(message="收藏笔记不存在")

    return success_response(data=collect_with_content, message="获取收藏笔记详情成功")


@router.post("/detail_by_content_id/{content_id}", response_model=BaseResponse[NoteCollectWithContent])
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

    collect_with_content = _get_collect_with_content(session, collect.uuid, current_user)

    return success_response(data=collect_with_content, message="获取收藏笔记详情成功")


@router.post("/create", response_model=BaseResponse[NoteCollectWithContent])
def create_note_collect(
    *,
    session: SessionDep,
    current_user: CurrentUserUnified,
    collect_in: NoteCollectCreateWithContent
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

    # 使用辅助函数创建包含内容的收藏笔记
    collect_with_content = _create_collect_with_content(session, current_user, collect_in)

    return success_response(
        data=collect_with_content,
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )


@router.post("/update/{uuid}", response_model=BaseResponse[NoteCollectWithContent])
def update_note_collect(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    collect_in: NoteCollectUpdateWithContent,
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

    # 使用辅助函数更新包含内容的收藏笔记
    collect_with_content = _update_collect_with_content(session, current_user, collect, collect_in)

    return success_response(data=collect_with_content, message=ResponseMessage.UPDATED)


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

    # 先删除相关的内容记录
    content_statement = select(NoteCollectContent).where(
        NoteCollectContent.collect_uuid == uuid
    )
    content = session.exec(content_statement).first()
    if content:
        session.delete(content)

    # 再删除主记录
    session.delete(collect)
    session.commit()
    return success_response(data=None, message=ResponseMessage.DELETED)


@router.post("/list", response_model=BaseResponse[list[NoteCollectWithContent]])
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

    # 批量获取包含内容的数据
    collects_with_content = _get_collects_with_content(session, collects)

    return success_response(data=collects_with_content, message="获取收藏笔记列表成功")


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


def _get_collects_with_content(
    session: SessionDep,
    collects: list[NoteCollect]
) -> list[NoteCollectWithContent]:
    """批量获取包含内容的收藏笔记列表"""
    if not collects:
        return []

    # 获取所有UUID
    collect_uuids = [collect.uuid for collect in collects]

    # 批量查询内容表
    content_statement = select(NoteCollectContent).where(
        NoteCollectContent.collect_uuid.in_(collect_uuids)
    )
    contents = session.exec(content_statement).all()

    # 构建UUID到内容的映射
    content_map = {content.collect_uuid: content for content in contents}

    # 合并数据
    result = []
    for collect in collects:
        collect_dict = collect.model_dump()
        content = content_map.get(collect.uuid)

        if content:
            collect_dict.update({
                "cn_content": content.cn_content,
                "en_content": content.en_content,
                "extdata": content.extdata
            })
        else:
            collect_dict.update({
                "cn_content": None,
                "en_content": None,
                "extdata": None
            })

        result.append(NoteCollectWithContent.model_validate(collect_dict))

    return result
