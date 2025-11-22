"""
统一认证依赖 - 支持JWT Token + 用户API Key双重认证
基于用户表qsa_usr_user中的api_key字段进行API Key认证
"""
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import select

from qiushuiai.core import security
from qiushuiai.core.config import settings
from qiushuiai.schemas.user import TokenPayload, UsrUserPublic, UsrUser
from qiushuiai.modules.user.deps import SessionDep


# 支持双重认证的Bearer Token
unified_security = HTTPBearer(auto_error=False)


def get_current_user_unified(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(unified_security)]
) -> UsrUserPublic:
    """
    统一认证：支持JWT Token或用户API Key

    认证顺序：
    1. 首先尝试JWT Token认证 - 解码JWT获取用户
    2. 如果JWT失败，尝试API Key认证 - 查询用户表api_key字段匹配

    API Key来源：qsa_usr_user表中的api_key字段值
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

    # 方式2：基于用户表api_key字段进行API Key认证
    api_key_user = session.exec(
        select(UsrUser).where(
            UsrUser.api_key == token,
            UsrUser.api_key.is_not(None),  # api_key不能为空
            UsrUser.is_active == True
        )
    ).first()

    if api_key_user:
        return UsrUserPublic.model_validate(api_key_user)

    # 两种认证都失败
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )


# 统一认证依赖别名
CurrentUserUnified = Annotated[UsrUserPublic, Depends(get_current_user_unified)]