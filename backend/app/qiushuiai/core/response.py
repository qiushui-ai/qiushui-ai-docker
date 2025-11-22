"""
统一API响应封装

提供标准化的API响应格式，包括成功响应、错误响应和分页响应等。
所有API接口都应该使用此模块的响应格式来保证前端处理的一致性。
"""

from typing import Any, Optional, TypeVar, Generic, List, Union
from pydantic import BaseModel, Field
from sqlmodel import SQLModel


# 响应状态常量
class ResponseStatus:
    """响应状态常量"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


# 响应状态码常量
class ResponseCode:
    """响应状态码常量"""
    # 成功状态码
    SUCCESS = 200
    CREATED = 201
    
    # 客户端错误状态码
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    VALIDATION_ERROR = 422
    
    # 服务器错误状态码
    INTERNAL_ERROR = 500
    SERVICE_UNAVAILABLE = 503


# 通用响应消息常量
class ResponseMessage:
    """通用响应消息常量"""
    # 成功消息
    SUCCESS = "操作成功"
    CREATED = "创建成功"
    UPDATED = "更新成功"
    DELETED = "删除成功"
    
    # 错误消息
    BAD_REQUEST = "请求参数错误"
    UNAUTHORIZED = "未授权访问"
    FORBIDDEN = "无权限访问"
    NOT_FOUND = "资源不存在"
    CONFLICT = "资源冲突"
    VALIDATION_ERROR = "数据验证失败"
    INTERNAL_ERROR = "服务器内部错误"
    SERVICE_UNAVAILABLE = "服务暂时不可用"


# 泛型类型变量
T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """基础响应模型"""
    status: str = Field(description="响应状态: success/error/warning")
    code: int = Field(description="响应状态码")
    message: str = Field(description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    timestamp: Optional[str] = Field(default=None, description="响应时间戳")


class PaginationInfo(BaseModel):
    """分页信息模型"""
    page: int = Field(description="当前页码")
    rows: int = Field(description="每页数量")
    total: int = Field(description="总记录数")
    pages: int = Field(description="总页数")


class PageResponse(BaseModel, Generic[T]):
    """分页响应数据模型"""
    items: List[T] = Field(description="数据列表")
    pagination: PaginationInfo = Field(description="分页信息")


class ListResponse(BaseModel, Generic[T]):
    """列表响应数据模型（无分页）"""
    items: List[T] = Field(description="数据列表")
    count: int = Field(description="数据总数")


def success_response(
    data: Optional[T] = None,
    message: str = ResponseMessage.SUCCESS,
    code: int = ResponseCode.SUCCESS
) -> BaseResponse[T]:
    """
    构建成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
        code: 响应状态码
        
    Returns:
        BaseResponse: 统一格式的成功响应
    """
    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        code=code,
        message=message,
        data=data
    )


def error_response(
    message: str = ResponseMessage.INTERNAL_ERROR,
    code: int = ResponseCode.INTERNAL_ERROR,
    data: Optional[T] = None
) -> BaseResponse[T]:
    """
    构建错误响应
    
    Args:
        message: 错误消息
        code: 错误状态码
        data: 额外的错误数据
        
    Returns:
        BaseResponse: 统一格式的错误响应
    """
    return BaseResponse(
        status=ResponseStatus.ERROR,
        code=code,
        message=message,
        data=data
    )


def page_response(
    items: List[T],
    page: int,
    rows: int,
    total: int,
    message: str = ResponseMessage.SUCCESS
) -> BaseResponse[PageResponse[T]]:
    """
    构建分页响应
    
    Args:
        items: 数据列表
        page: 当前页码
        rows: 每页数量
        total: 总记录数
        message: 响应消息
        
    Returns:
        BaseResponse: 统一格式的分页响应
    """
    pages = (total + rows - 1) // rows if rows > 0 else 0
    
    pagination_data = PageResponse(
        items=items,
        pagination=PaginationInfo(
            page=page,
            rows=rows,
            total=total,
            pages=pages
        )
    )
    
    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        code=ResponseCode.SUCCESS,
        message=message,
        data=pagination_data
    )


def list_response(
    items: List[T],
    message: str = ResponseMessage.SUCCESS
) -> BaseResponse[ListResponse[T]]:
    """
    构建列表响应（无分页）
    
    Args:
        items: 数据列表
        message: 响应消息
        
    Returns:
        BaseResponse: 统一格式的列表响应
    """
    list_data = ListResponse(
        items=items,
        count=len(items)
    )
    
    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        code=ResponseCode.SUCCESS,
        message=message,
        data=list_data
    ) 