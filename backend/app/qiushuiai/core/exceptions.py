"""
全局异常处理器

提供统一的异常处理机制，确保所有错误都返回一致的响应格式。
"""

import logging
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .response import (
    BaseResponse,
    error_response,
    ResponseCode,
    ResponseMessage
)

logger = logging.getLogger(__name__)


class APIException(Exception):
    """自定义API异常基类"""
    
    def __init__(
        self,
        message: str = ResponseMessage.INTERNAL_ERROR,
        code: int = ResponseCode.INTERNAL_ERROR,
        data: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(self.message)


class BusinessException(APIException):
    """业务异常"""
    
    def __init__(
        self,
        message: str = "业务处理失败",
        code: int = ResponseCode.BAD_REQUEST,
        data: Optional[Any] = None
    ):
        super().__init__(message, code, data)


class ResourceNotFoundException(APIException):
    """资源不存在异常"""
    
    def __init__(
        self,
        message: str = ResponseMessage.NOT_FOUND,
        data: Optional[Any] = None
    ):
        super().__init__(message, ResponseCode.NOT_FOUND, data)


class UnauthorizedException(APIException):
    """未授权异常"""
    
    def __init__(
        self,
        message: str = ResponseMessage.UNAUTHORIZED,
        data: Optional[Any] = None
    ):
        super().__init__(message, ResponseCode.UNAUTHORIZED, data)


class ForbiddenException(APIException):
    """权限不足异常"""
    
    def __init__(
        self,
        message: str = ResponseMessage.FORBIDDEN,
        data: Optional[Any] = None
    ):
        super().__init__(message, ResponseCode.FORBIDDEN, data)


class ValidationException(APIException):
    """数据验证异常"""
    
    def __init__(
        self,
        message: str = ResponseMessage.VALIDATION_ERROR,
        data: Optional[Any] = None
    ):
        super().__init__(message, ResponseCode.VALIDATION_ERROR, data)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTPException异常处理器"""
    logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
    
    # 根据状态码选择相应的错误响应
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        response = error_response(message=str(exc.detail), code=ResponseCode.NOT_FOUND)
    elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
        response = error_response(message=str(exc.detail), code=ResponseCode.UNAUTHORIZED)
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        response = error_response(message=str(exc.detail), code=ResponseCode.FORBIDDEN)
    elif exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        response = error_response(message=str(exc.detail), code=ResponseCode.VALIDATION_ERROR)
    else:
        response = error_response(
            message=str(exc.detail),
            code=exc.status_code
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """请求验证异常处理器"""
    logger.warning(f"ValidationError: {exc.errors()}")
    
    # 格式化验证错误信息
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    response = error_response(
        message="请求数据验证失败",
        code=ResponseCode.VALIDATION_ERROR,
        data=errors
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump()
    )


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """自定义API异常处理器"""
    logger.warning(f"APIException: {exc.code} - {exc.message}")
    
    response = error_response(
        message=exc.message,
        code=exc.code,
        data=exc.data
    )
    
    return JSONResponse(
        status_code=exc.code,
        content=response.model_dump()
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """数据库完整性约束异常处理器"""
    logger.error(f"IntegrityError: {str(exc)}")
    
    # 解析常见的完整性约束错误
    error_message = "数据操作失败"
    if "duplicate key" in str(exc).lower():
        error_message = "数据已存在，不能重复创建"
    elif "foreign key" in str(exc).lower():
        error_message = "关联数据不存在，无法操作"
    elif "not null" in str(exc).lower():
        error_message = "必填字段不能为空"
    
    response = error_response(
        message=error_message,
        code=ResponseCode.CONFLICT
    )
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.model_dump()
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """SQLAlchemy异常处理器"""
    logger.error(f"SQLAlchemyError: {str(exc)}")
    
    response = error_response(
        message="数据库操作失败",
        code=ResponseCode.INTERNAL_ERROR
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}", exc_info=True)
    
    response = error_response(
        message=ResponseMessage.INTERNAL_ERROR,
        code=ResponseCode.INTERNAL_ERROR
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump()
    )


def register_exception_handlers(app) -> None:
    """注册所有异常处理器"""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    app.add_exception_handler(Exception, general_exception_handler) 