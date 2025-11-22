from typing import Any, Annotated
from datetime import datetime
import uuid as uuid_module
import json

from fastapi import APIRouter, Body
from sqlmodel import func, select
from sqlalchemy import text

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
from qiushuiai.schemas.note import (
    NoteMine,
    NoteMineCreate,
    NoteMinePublic,
    NoteMineUpdate,
    NoteMineWithTags,
    TagInfo,
)
from qiushuiai.modules.note.markdown_parser import extract_tags_from_markdown
from qiushuiai.modules.note.tag_hierarchy_service import TagHierarchyService


router = APIRouter(prefix="/note/mine", tags=["note_mine"])


@router.post("/page", response_model=BaseResponse[PageResponse[NoteMinePublic]])
def page_note_mine(
    session: SessionDep,
    current_user: CurrentUser,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取我的笔记列表（分页）。"""
    # 提取参数，设置默认值
    page = request_data.get("page", 1)
    rows = request_data.get("rows", 20)
    keyword = request_data.get("keyword")
    status = request_data.get("status")  # 根据状态筛选
    tag_path = request_data.get("tag_path")  # 根据标签路径筛选

    # 构建基础查询
    statement = select(NoteMine)

    # 应用通用过滤条件
    statement = apply_common_filters(
        statement=statement,
        model=NoteMine,
        current_user=current_user
    )

    # 根据状态筛选
    if status is not None:
        statement = statement.where(NoteMine.status == status)

    # 根据标签路径筛选
    if tag_path is not None and tag_path.strip():
        # 使用 PostgreSQL JSONB @> 操作符检查 tag_names 数组中是否包含指定的 tag_path
        # tags->'tag_names' 返回 JSON 类型，需要转换为 JSONB 才能使用 @> 操作符
        # @> 操作符检查左侧 JSONB 是否包含右侧 JSONB
        tag_path_value = tag_path.strip()
        # 使用 json.dumps 安全地创建 JSON 数组
        tag_path_json = json.dumps([tag_path_value])
        statement = statement.where(
            text(f"(tags->'tag_names')::jsonb @> '{tag_path_json}'::jsonb")
        )

    # 应用关键词搜索
    statement = apply_keyword_search(
        statement=statement,
        model=NoteMine,
        keyword=keyword,
        search_fields=["title", "content"]
    )

    # 构建计数查询
    count_statement = get_count_query(statement, NoteMine)
    count = session.exec(count_statement).one()

    # 添加排序
    statement = build_order_by(
        statement=statement,
        model=NoteMine,
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
    notes = session.exec(statement).all()

    # 使用标准分页响应格式
    return page_response(
        items=notes,
        page=page,
        rows=rows,
        total=count,
        message="获取我的笔记列表成功"
    )


@router.post("/detail/{uuid}", response_model=BaseResponse[NoteMinePublic])
def read_note_mine(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个笔记。"""
    statement = select(NoteMine).where(NoteMine.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=NoteMine,
        current_user=current_user
    )
    note = session.exec(statement).first()

    if not note:
        raise ResourceNotFoundException(message="笔记不存在")

    return success_response(data=note, message="获取笔记详情成功")


@router.post("/create", response_model=BaseResponse[NoteMineWithTags])
def create_note_mine(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    note_in: NoteMineCreate
) -> Any:
    """
    创建新笔记。

    自动从 Markdown 内容中提取标签，并合并用户手动输入的标签。
    标签会自动保存到 qsa_note_tag 表中（包括层级关系）。
    返回的数据中包含标签的详细信息（id、tag_name、tag_path等）。
    """
    note_data = note_in.model_dump()

    # 1. 从 Markdown 内容中提取标签
    auto_tags = extract_tags_from_markdown(note_data.get("content", ""))

    # 2. 合并用户手动输入的标签
    manual_tags = []
    if note_data.get("tags"):
        # tags 是一个对象 {"tag_ids": [...], "tag_names": [...]}
        tag_obj = note_data.get("tags", {})
        if isinstance(tag_obj, dict):
            manual_tags = tag_obj.get("tag_names", [])
        elif isinstance(tag_obj, list):
            manual_tags = tag_obj

    # 合并并去重
    all_tags = list(set(auto_tags + manual_tags))

    # 3. 确保所有标签在 qsa_note_tag 表中存在（包括层级）
    # 返回每个标签是否是新创建的
    creation_status = TagHierarchyService.ensure_tags_batch(
        db=session,
        tag_list=all_tags,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )

    # 4. 获取标签的详细信息
    tag_details_raw = TagHierarchyService.get_tags_info_by_names(
        db=session,
        tag_names=all_tags,
        tenant_id=current_user.tenant_id
    )

    # 5. 为每个标签添加 is_new 标识
    tag_details = []
    for tag in tag_details_raw:
        tag_dict = tag.copy()
        tag_dict["is_new"] = creation_status.get(tag["full_path"], False)
        tag_details.append(tag_dict)

    # 6. 更新 note_data 中的 tags 字段（保存为 JSONB 字典）
    note_data["tags"] = {
        "tag_names": all_tags
    }

    # 使用通用函数更新公共字段
    note_data = update_common_fields(
        data=note_data,
        current_user=current_user,
        is_create=True
    )

    note = NoteMine.model_validate(note_data)
    session.add(note)
    session.commit()
    session.refresh(note)

    # 7. 构建包含标签详情的响应
    note_with_tags = NoteMineWithTags.model_validate(note)
    note_with_tags.tag_details = [TagInfo.model_validate(tag) for tag in tag_details]

    return success_response(
        data=note_with_tags,
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )


@router.post("/update/{uuid}", response_model=BaseResponse[NoteMineWithTags])
def update_note_mine(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    note_in: NoteMineUpdate,
) -> Any:
    """
    更新笔记信息。

    如果更新了内容或提供了标签字段，会处理标签并更新 qsa_note_tag 表。
    - 如果更新了内容，会从内容中自动提取标签
    - 如果提供了标签字段，会使用提供的标签
    - 自动提取的标签和手动提供的标签会合并去重
    返回的数据中包含标签的详细信息（id、tag_name、tag_path等）。
    """
    statement = select(NoteMine).where(NoteMine.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=NoteMine,
        current_user=current_user
    )
    note = session.exec(statement).first()

    if not note:
        raise ResourceNotFoundException(message="笔记不存在")

    update_dict = note_in.model_dump(exclude_unset=True)
    tag_details = None

    # 判断是否需要处理标签：更新了内容或提供了标签字段
    should_process_tags = "content" in update_dict or "tags" in update_dict

    if should_process_tags:
        # 1. 从新的内容中提取标签（如果更新了内容）
        auto_tags = []
        if "content" in update_dict:
            auto_tags = extract_tags_from_markdown(update_dict["content"])

        # 2. 获取用户手动输入的标签
        manual_tags = []
        if "tags" in update_dict:
            tag_obj = update_dict.get("tags", {})
            if isinstance(tag_obj, dict):
                manual_tags = tag_obj.get("tag_names", [])
            elif isinstance(tag_obj, list):
                manual_tags = tag_obj
        else:
            # 如果没有提供新标签但更新了内容，保留原有标签
            if "content" in update_dict:
                if note.tags and isinstance(note.tags, dict):
                    manual_tags = note.tags.get("tag_names", [])
                else:
                    manual_tags = []

        # 合并并去重
        all_tags = list(set(auto_tags + manual_tags))

        # 3. 确保所有标签在 qsa_note_tag 表中存在
        # 返回每个标签是否是新创建的
        creation_status = TagHierarchyService.ensure_tags_batch(
            db=session,
            tag_list=all_tags,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id
        )

        # 4. 获取标签的详细信息
        tag_details_raw = TagHierarchyService.get_tags_info_by_names(
            db=session,
            tag_names=all_tags,
            tenant_id=current_user.tenant_id
        )

        # 5. 为每个标签添加 is_new 标识
        tag_details = []
        for tag in tag_details_raw:
            tag_dict = tag.copy()
            tag_dict["is_new"] = creation_status.get(tag["full_path"], False)
            tag_details.append(tag_dict)

        # 6. 更新标签字段（保存为字典）
        update_dict["tags"] = {
            "tag_names": all_tags
        }

    # 使用通用函数更新公共字段
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )

    note.sqlmodel_update(update_dict)
    session.add(note)
    session.commit()
    session.refresh(note)

    # 构建包含标签详情的响应
    note_with_tags = NoteMineWithTags.model_validate(note)
    if tag_details:
        note_with_tags.tag_details = [TagInfo.model_validate(tag) for tag in tag_details]

    return success_response(data=note_with_tags, message=ResponseMessage.UPDATED)


@router.post("/delete/{uuid}", response_model=BaseResponse[None])
def delete_note_mine(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """删除笔记。"""
    statement = select(NoteMine).where(NoteMine.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=NoteMine,
        current_user=current_user
    )
    note = session.exec(statement).first()

    if not note:
        raise ResourceNotFoundException(message="笔记不存在")

    session.delete(note)
    session.commit()
    return success_response(data=None, message=ResponseMessage.DELETED)


@router.post("/list", response_model=BaseResponse[list[NoteMinePublic]])
def list_note_mine(
    session: SessionDep,
    current_user: CurrentUser,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取我的笔记列表（不分页）。"""
    status = request_data.get("status")  # 根据状态筛选
    collect_id = request_data.get("collect_id")  # 根据关联收藏筛选

    # 构建基础查询
    statement = select(NoteMine)

    # 应用通用过滤条件
    statement = apply_common_filters(
        statement=statement,
        model=NoteMine,
        current_user=current_user
    )

    # 根据状态筛选
    if status is not None:
        statement = statement.where(NoteMine.status == status)

    # 根据关联收藏筛选
    if collect_id is not None:
        statement = statement.where(NoteMine.collect_id == collect_id)

    # 添加排序
    statement = build_order_by(
        statement=statement,
        model=NoteMine,
        order_by="id",
        order_direction="desc"
    )

    # 执行查询
    notes = session.exec(statement).all()

    return success_response(data=notes, message="获取我的笔记列表成功")
