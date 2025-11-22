from typing import Any, TypeVar, Type, Optional
from datetime import datetime

from sqlmodel import select, func, and_, or_
from sqlalchemy.sql import Select
from sqlalchemy import Text

from qiushuiai.modules.user.deps import CurrentUser

# 泛型类型变量，用于类型提示
ModelType = TypeVar("ModelType")


def add_soft_delete_filter(statement: Select, model: Type[ModelType]) -> Select:
    """
    添加软删除过滤条件。
    
    Args:
        statement (Select): 查询语句
        model (Type[ModelType]): 模型类
    
    Returns:
        Select: 添加了软删除过滤条件的查询语句
    """
    if hasattr(model, 'is_del'):
        statement = statement.where(model.is_del == False)
    return statement


def add_tenant_filter(
    statement: Select, 
    model: Type[ModelType], 
    tenant_id: Optional[int] = None
) -> Select:
    """
    添加租户过滤条件。
    
    Args:
        statement (Select): 查询语句
        model (Type[ModelType]): 模型类
        tenant_id (Optional[int]): 租户ID，如果为None则不添加租户过滤
    
    Returns:
        Select: 添加了租户过滤条件的查询语句
    """
    print(f"---add_tenant_filter: {model}, {tenant_id},{hasattr(model, 'tenant_id')}")
    if hasattr(model, 'tenant_id'):
        statement = statement.where(model.tenant_id == tenant_id)
    return statement


def add_ownership_filter(
    statement: Select, 
    model: Type[ModelType], 
    current_user: CurrentUser,
    created_at: Optional[int] = None
) -> Select:
    """
    添加数据所有权过滤条件，支持查看公开数据。
    
    Args:
        statement (Select): 查询语句
        model (Type[ModelType]): 模型类
        current_user (CurrentUser): 当前登录用户
        allow_public (bool): 是否允许查看公开数据
    
    Returns:
        Select: 添加了所有权过滤条件的查询语句
    """
    # if current_user.is_superuser:
    #     return statement
    
    if created_at is not None and hasattr(model, 'created_at'):
        statement = statement.where(model.created_by == current_user.id)
    
    return statement


def apply_common_filters(
    statement: Select,
    model: Type[ModelType],
    current_user: CurrentUser,

) -> Select:
    """
    应用通用的过滤条件组合。
    
    Args:
        statement (Select): 查询语句
        model (Type[ModelType]): 模型类
        current_user (CurrentUser): 当前登录用户
        tenant_id (Optional[int]): 租户ID
        include_soft_deleted (bool): 是否包含软删除的数据
    
    Returns:
        Select: 应用了所有过滤条件的查询语句
    """
    # 软删除过滤
    statement = add_soft_delete_filter(statement, model)
    
    # 租户过滤
    statement = add_tenant_filter(statement, model, current_user.tenant_id)
    
    # 所有权过滤
    statement = add_ownership_filter(statement, model, current_user)
    
    
    return statement


def apply_pagination(
    statement: Select,
    page: int = 1,
    page_size: int = 20,
    max_page_size: int = 100
) -> tuple[Select, int, int]:
    """
    应用分页条件。
    
    Args:
        statement (Select): 查询语句
        page (int): 页码，从1开始
        page_size (int): 每页大小
        max_page_size (int): 最大每页大小
    
    Returns:
        tuple[Select, int, int]: (分页后的查询语句, 偏移量, 限制数量)
    """
    # 限制每页大小
    page_size = min(page_size, max_page_size)
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 应用分页
    statement = statement.offset(offset).limit(page_size)
    
    return statement, offset, page_size


def build_order_by(
    statement: Select,
    model: Type[ModelType],
    order_by: Optional[str] = None,
    order_direction: str = "desc"
) -> Select:
    """
    构建排序条件。
    
    Args:
        statement (Select): 查询语句
        model (Type[ModelType]): 模型类
        order_by (Optional[str]): 排序字段，默认为"created_at"
        order_direction (str): 排序方向，"asc"或"desc"
    
    Returns:
        Select: 添加了排序条件的查询语句
    """
    if order_by is None:
        order_by = "created_at"
    
    if not hasattr(model, order_by):
        # 如果指定字段不存在，回退到created_at
        if hasattr(model, "created_at"):
            order_by = "created_at"
        else:
            return statement
    
    order_column = getattr(model, order_by)
    
    if order_direction.lower() == "asc":
        statement = statement.order_by(order_column.asc())
    else:
        statement = statement.order_by(order_column.desc())
    
    return statement


def get_count_query(statement: Select, model: Type[ModelType]) -> Select:
    """
    从数据查询语句构建计数查询。
    
    Args:
        statement (Select): 原始查询语句
        model (Type[ModelType]): 模型类
    
    Returns:
        Select: 计数查询语句
    """
    # 移除原有的order_by, limit, offset条件
    count_statement = statement.limit(None).offset(None).order_by(None)
    
    # 构建计数查询
    count_statement = select(func.count()).select_from(count_statement.subquery())
    
    return count_statement


def update_common_fields(
    data: dict[str, Any],
    current_user: CurrentUser,
    is_create: bool = False
) -> dict[str, Any]:
    """
    更新通用字段（创建时间、更新时间、创建者、更新者）。
    
    Args:
        data (dict[str, Any]): 要更新的数据字典
        current_user (CurrentUser): 当前登录用户
        is_create (bool): 是否为创建操作
    
    Returns:
        dict[str, Any]: 更新后的数据字典
    """
    now = datetime.now()
    
    if is_create:
        data.update({
            "tenant_id": current_user.tenant_id,
            "created_by": current_user.id,
            "created_at": now,
        })
    
    data.update({
        "updated_by": current_user.id,
        "updated_at": now
    })
    
    return data


def apply_keyword_search(
    statement: Select,
    model: Type[ModelType],
    keyword: Optional[str] = None,
    search_fields: Optional[list[str]] = None
) -> Select:
    """
    应用关键词搜索过滤条件。
    
    Args:
        statement (Select): 查询语句
        model (Type[ModelType]): 模型类
        keyword (Optional[str]): 搜索关键词
        search_fields (Optional[list[str]]): 要搜索的字段列表
    
    Returns:
        Select: 添加了搜索条件的查询语句
    """
    if not keyword or not keyword.strip():
        return statement
    
    if not search_fields:
        return statement
    
    keyword_pattern = f"%{keyword.strip()}%"
    search_conditions = []
    
    for field_name in search_fields:
        if hasattr(model, field_name):
            field = getattr(model, field_name)
            
            # 对所有指定字段使用 ilike 搜索（不区分大小写）
            search_conditions.append(func.cast(field, Text).ilike(keyword_pattern))
    
    if search_conditions:
        statement = statement.where(or_(*search_conditions))
    
    return statement