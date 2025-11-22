"""
统一认证依赖 - 优化版：基于用户表api_key字段
"""
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session, select

from qiushuiai.core import security
from qiushuiai.core.config import settings
from qiushuiai.schemas.user import TokenPayload, UsrUserPublic, UsrUser
from qiushuiai.modules.user.deps import SessionDep


# 支持双重认证的Bearer Token
unified_security = HTTPBearer(auto_error=False)


def get_current_user_unified_v2(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(unified_security)]
) -> UsrUserPublic:
    """
    统一认证V2：支持JWT Token或用户API Key

    认证顺序：
    1. 首先尝试JWT Token认证
    2. 如果JWT失败，尝试用户表中的api_key字段认证
    3. 如果都失败，尝试系统级API Key认证（兜底）
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证信息缺失",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # 方式1：尝试JWT Token认证
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)

        # 查询JWT用户
        user = session.get(UsrUser, token_data.sub)
        if user and user.is_active:
            return UsrUserPublic.model_validate(user)

    except (InvalidTokenError, ValidationError):
        # JWT认证失败，继续尝试API Key
        pass

    # 方式2：尝试用户表中的API Key认证
    api_key_user = session.exec(
        select(UsrUser).where(
            UsrUser.api_key == token,
            UsrUser.is_active == True
        )
    ).first()

    if api_key_user:
        return UsrUserPublic.model_validate(api_key_user)

    # 方式3：尝试系统级API Key认证（兜底，可选）
    if settings.API_KEY and token == settings.API_KEY:
        # 查找默认系统用户
        system_user = session.exec(
            select(UsrUser).where(
                UsrUser.tenant_id == 1,
                UsrUser.role == "admin",
                UsrUser.is_active == True
            )
        ).first()

        if system_user:
            return UsrUserPublic.model_validate(system_user)

    # 所有认证都失败
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )


# 统一认证依赖别名
CurrentUserUnifiedV2 = Annotated[UsrUserPublic, Depends(get_current_user_unified_v2)]