from typing import Any, Annotated
from datetime import datetime
import uuid as uuid_module

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import select
from sqlalchemy import and_
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
    NoteCollectCreater,
    NoteCollectCreaterCreate,
    NoteCollectCreaterPublic,
    NoteCollectCreaterUpdate,
)


router = APIRouter(prefix="/note/collect/creater", tags=["note_collect_creater"])


@router.post("/page", response_model=BaseResponse[PageResponse[NoteCollectCreaterPublic]])
def page_note_collect_creater(
    session: SessionDep,
    current_user: CurrentUserUnified,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取收藏创作者列表（分页）。

    支持筛选条件：
    - keyword: 关键词搜索（博主名称、用户名、网址）
    - platform: 平台筛选
    - is_collecting: 是否采集筛选
    - status: 状态筛选
    """
    # 提取参数，设置默认值
    page = request_data.get("page", 1)
    rows = request_data.get("rows", 20)
    keyword = request_data.get("keyword")
    platform = request_data.get("platform")
    is_collecting = request_data.get("is_collecting")
    status = request_data.get("status")

    # 构建基础查询
    statement = select(NoteCollectCreater)

    # 应用通用过滤条件（租户隔离）
    statement = apply_common_filters(
        statement=statement,
        model=NoteCollectCreater,
        current_user=current_user
    )

    # 根据平台筛选
    if platform is not None and platform.strip():
        statement = statement.where(NoteCollectCreater.platform == platform.strip())

    # 根据采集状态筛选
    if is_collecting is not None:
        statement = statement.where(NoteCollectCreater.is_collecting == is_collecting)

    # 根据状态筛选
    if status is not None and status.strip():
        statement = statement.where(NoteCollectCreater.status == status.strip())

    # 应用关键词搜索
    statement = apply_keyword_search(
        statement=statement,
        model=NoteCollectCreater,
        keyword=keyword,
        search_fields=["blogger_name", "username", "website_url"]
    )

    # 构建计数查询
    count_statement = get_count_query(statement, NoteCollectCreater)
    count = session.exec(count_statement).one()

    # 添加排序
    statement = build_order_by(
        statement=statement,
        model=NoteCollectCreater,
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
    creaters = session.exec(statement).all()

    # 使用标准分页响应格式
    return page_response(
        items=creaters,
        page=page,
        rows=rows,
        total=count,
        message="获取收藏创作者列表成功"
    )


@router.post("/detail/{uuid}", response_model=BaseResponse[NoteCollectCreaterPublic])
def read_note_collect_creater(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个收藏创作者。"""
    statement = select(NoteCollectCreater).where(NoteCollectCreater.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=NoteCollectCreater,
        current_user=current_user
    )
    creater = session.exec(statement).first()

    if not creater:
        raise ResourceNotFoundException(message="收藏创作者不存在")

    return success_response(data=creater, message="获取收藏创作者详情成功")


@router.post("/create", response_model=BaseResponse[NoteCollectCreaterPublic])
def create_note_collect_creater(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    creater_in: NoteCollectCreaterCreate
) -> Any:
    """创建新的收藏创作者。

    会检查 (tenant_id, platform, username) 的唯一性约束。
    """
    creater_data = creater_in.model_dump()

    # 检查唯一性约束：同一租户下同一平台的用户名不能重复
    existing = session.exec(
        select(NoteCollectCreater).where(
            and_(
                NoteCollectCreater.tenant_id == current_user.tenant_id,
                NoteCollectCreater.platform == creater_data["platform"],
                NoteCollectCreater.username == creater_data["username"]
            )
        )
    ).first()

    if existing:
        raise ValidationException(
            message=f"平台 {creater_data['platform']} 下的用户名 {creater_data['username']} 已存在"
        )

    # 使用通用函数更新公共字段
    creater_data = update_common_fields(
        data=creater_data,
        current_user=current_user,
        is_create=True
    )

    creater = NoteCollectCreater.model_validate(creater_data)
    session.add(creater)
    session.commit()
    session.refresh(creater)

    return success_response(
        data=creater,
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )


@router.post("/update/{uuid}", response_model=BaseResponse[NoteCollectCreaterPublic])
def update_note_collect_creater(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    creater_in: NoteCollectCreaterUpdate,
) -> Any:
    """更新收藏创作者信息。

    如果更新了 platform 或 username，会检查唯一性约束。
    """
    statement = select(NoteCollectCreater).where(NoteCollectCreater.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=NoteCollectCreater,
        current_user=current_user
    )
    creater = session.exec(statement).first()

    if not creater:
        raise ResourceNotFoundException(message="收藏创作者不存在")

    update_dict = creater_in.model_dump(exclude_unset=True)

    # 如果更新了平台或用户名，检查唯一性约束
    if "platform" in update_dict or "username" in update_dict:
        new_platform = update_dict.get("platform", creater.platform)
        new_username = update_dict.get("username", creater.username)

        # 检查是否与现有记录冲突（排除自身）
        existing = session.exec(
            select(NoteCollectCreater).where(
                and_(
                    NoteCollectCreater.tenant_id == current_user.tenant_id,
                    NoteCollectCreater.platform == new_platform,
                    NoteCollectCreater.username == new_username,
                    NoteCollectCreater.id != creater.id
                )
            )
        ).first()

        if existing:
            raise ValidationException(
                message=f"平台 {new_platform} 下的用户名 {new_username} 已存在"
            )

    # 使用通用函数更新公共字段
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )

    creater.sqlmodel_update(update_dict)
    session.add(creater)
    session.commit()
    session.refresh(creater)

    return success_response(data=creater, message=ResponseMessage.UPDATED)


@router.post("/delete/{uuid}", response_model=BaseResponse[None])
def delete_note_collect_creater(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """删除收藏创作者。"""
    statement = select(NoteCollectCreater).where(NoteCollectCreater.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=NoteCollectCreater,
        current_user=current_user
    )
    creater = session.exec(statement).first()

    if not creater:
        raise ResourceNotFoundException(message="收藏创作者不存在")

    session.delete(creater)
    session.commit()
    return success_response(data=None, message=ResponseMessage.DELETED)


@router.post("/list", response_model=BaseResponse[list[NoteCollectCreaterPublic]])
def list_note_collect_creater(
    session: SessionDep,
    current_user: CurrentUser,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取收藏创作者列表（不分页）。

    支持筛选条件：
    - platform: 平台筛选
    - is_collecting: 是否采集筛选
    - status: 状态筛选
    """
    platform = request_data.get("platform")
    is_collecting = request_data.get("is_collecting")
    status = request_data.get("status")

    # 构建基础查询
    statement = select(NoteCollectCreater)

    # 应用通用过滤条件（租户隔离）
    statement = apply_common_filters(
        statement=statement,
        model=NoteCollectCreater,
        current_user=current_user
    )

    # 根据平台筛选
    if platform is not None and platform.strip():
        statement = statement.where(NoteCollectCreater.platform == platform.strip())

    # 根据采集状态筛选
    if is_collecting is not None:
        statement = statement.where(NoteCollectCreater.is_collecting == is_collecting)

    # 根据状态筛选
    if status is not None and status.strip():
        statement = statement.where(NoteCollectCreater.status == status.strip())

    # 添加排序
    statement = build_order_by(
        statement=statement,
        model=NoteCollectCreater,
        order_by="id",
        order_direction="desc"
    )

    # 执行查询
    creaters = session.exec(statement).all()

    return success_response(data=creaters, message="获取收藏创作者列表成功")

