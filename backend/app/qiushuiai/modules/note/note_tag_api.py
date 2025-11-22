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
from qiushuiai.schemas.note import (
    NoteTag,
    NoteTagCreate,
    NoteTagPublic,
    NoteTagSimple,
    NoteTagUpdate,
    NoteTagBatchSortOrderUpdate,
)
from qiushuiai.modules.note.note_tag_service import NoteTagService


router = APIRouter(prefix="/note/tag", tags=["note_tag"])


@router.post("/tree", response_model=BaseResponse[list])
def get_note_tag_tree(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """获取笔记标签树形结构。"""
    # 使用服务层获取树形结构
    service = NoteTagService(session)
    tree_data = service.get_tree(current_user)

    return success_response(
        data=tree_data,
        message="获取笔记标签树形结构成功"
    )


@router.post("/detail/{uuid}", response_model=BaseResponse[NoteTagPublic])
def read_note_tag(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个笔记标签。"""
    service = NoteTagService(session)
    tag = service.get_tag_by_uuid(uuid)

    return success_response(data=tag, message="获取笔记标签详情成功")


@router.post("/create", response_model=BaseResponse[NoteTagPublic])
def create_note_tag(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    tag_in: NoteTagCreate
) -> Any:
    """创建新笔记标签。

    自动处理父节点赋值：
    - 如果提供了 parent_id，会自动验证父节点存在性
    - 自动计算并设置 tag_path（标签路径）
    - 自动计算并设置 level（层级）
    - 支持创建根节点（不提供 parent_id）或子节点（提供 parent_id）
    """
    service = NoteTagService(session)
    tag = service.create_tag(tag_in, current_user)

    return success_response(
        data=tag,
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )


@router.post("/update/{uuid}", response_model=BaseResponse[NoteTagPublic])
def update_note_tag(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    tag_in: NoteTagUpdate,
) -> Any:
    """更新笔记标签信息。

    自动处理：
    - 如果修改了 parent_id 或 tag_name，会自动更新所有子标签的 tag_path 和 level
    - 自动验证不会产生循环引用
    """
    service = NoteTagService(session)
    tag = service.update_tag(uuid, tag_in, current_user)

    return success_response(data=tag, message=ResponseMessage.UPDATED)


@router.post("/batch-update-sort-order", response_model=BaseResponse[dict])
def batch_update_sort_order(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    request_data: NoteTagBatchSortOrderUpdate
) -> Any:
    """批量更新标签排序顺序。
    
    根据uuids数组的顺序，将每个标签的sort_order设置为对应的索引。
    例如：uuids = ["uuid1", "uuid2", "uuid3"] 
    会设置 uuid1.sort_order=0, uuid2.sort_order=1, uuid3.sort_order=2
    
    使用事务确保操作的原子性。
    """
    service = NoteTagService(session)
    result = service.batch_update_sort_order(request_data.uuids, current_user)
    
    return success_response(
        data=result,
        message=f"成功更新 {result['updated_count']} 个标签的排序顺序"
    )


@router.post("/delete/{uuid}", response_model=BaseResponse[None])
def delete_note_tag(
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID
) -> Any:
    """删除笔记标签及其所有子标签（级联删除）。"""
    service = NoteTagService(session)
    service.delete_tag(uuid)

    return success_response(data=None, message=ResponseMessage.DELETED)


@router.post("/page", response_model=BaseResponse[PageResponse[NoteTagPublic]])
def page_note_tag(
    session: SessionDep,
    current_user: CurrentUser,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取笔记标签列表（分页）。"""
    # 提取参数，设置默认值
    page = request_data.get("page", 1)
    rows = request_data.get("rows", 20)
    keyword = request_data.get("keyword")
    parent_id = request_data.get("parent_id")  # 根据父标签筛选

    # 构建基础查询
    statement = select(NoteTag)

    # 应用通用过滤条件
    statement = apply_common_filters(
        statement=statement,
        model=NoteTag,
        current_user=current_user
    )

    # 根据父标签筛选
    if parent_id is not None:
        if parent_id == 0:  # 0 表示查询根标签
            statement = statement.where(NoteTag.parent_id.is_(None))
        else:
            statement = statement.where(NoteTag.parent_id == parent_id)

    # 应用关键词搜索
    statement = apply_keyword_search(
        statement=statement,
        model=NoteTag,
        keyword=keyword,
        search_fields=["tag_name", "tag_path"]
    )

    # 构建计数查询
    count_statement = get_count_query(statement, NoteTag)
    count = session.exec(count_statement).one()

    # 添加排序 - 优先按sort_order排序，然后按id正序
    statement = build_order_by(
        statement=statement,
        model=NoteTag,
        order_by="sort_order",
        order_direction="asc"
    )
    statement = statement.order_by(NoteTag.id.asc())

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
        message="获取笔记标签列表成功"
    )


@router.post("/list", response_model=BaseResponse[list[NoteTagSimple]])
def list_note_tag(
    session: SessionDep,
    current_user: CurrentUser,
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取笔记标签列表（不分页），只返回 uuid 和 full_name。"""
    parent_id = request_data.get("parent_id")  # 根据父标签筛选

    # 构建基础查询
    statement = select(NoteTag)

    # 应用通用过滤条件
    statement = apply_common_filters(
        statement=statement,
        model=NoteTag,
        current_user=current_user
    )

    # 根据父标签筛选
    if parent_id is not None:
        if parent_id == 0:  # 0 表示查询根标签
            statement = statement.where(NoteTag.parent_id.is_(None))
        else:
            statement = statement.where(NoteTag.parent_id == parent_id)

    # 添加排序 - 优先按sort_order排序，然后按id正序
    statement = build_order_by(
        statement=statement,
        model=NoteTag,
        order_by="sort_order",
        order_direction="asc"
    )
    statement = statement.order_by(NoteTag.id.asc())

    # 执行查询
    tags = session.exec(statement).all()

    # 为每个标签计算 full_name 并构建简化响应
    result_tags = []
    for tag in tags:
        tag_path = tag.tag_path or ""
        tag_name = tag.tag_name or ""
        
        # 如果 tag_path 第一个字符是 /，去掉它
        if tag_path.startswith("/"):
            tag_path = tag_path[1:]
        
        # 组合 full_name
        if tag_path:
            full_name = f"{tag_path}/{tag_name}"
        else:
            full_name = tag_name
        
        # 创建简化的标签响应，只包含 uuid 和 full_name
        tag_simple = NoteTagSimple(uuid=tag.uuid, full_name=full_name)
        result_tags.append(tag_simple)

    return success_response(data=result_tags, message="获取笔记标签列表成功")
