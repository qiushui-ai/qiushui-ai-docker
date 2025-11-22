from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session, select

from qiushuiai.core import security
from qiushuiai.core.config import settings
from qiushuiai.core.db import engine
from qiushuiai.schemas.user import TokenPayload, UsrUserPublic, UsrUser

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/user/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session    


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> UsrUserPublic:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 修正：使用 UsrUser 数据库模型而不是 UsrUserPublic schema
    user = session.get(UsrUser, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # 返回 UsrUserPublic schema
    return UsrUserPublic.model_validate(user)


CurrentUser = Annotated[UsrUserPublic, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> UsrUserPublic:
    # if not current_user.is_superuser:
    #     raise HTTPException(
    #         status_code=403, detail="The user doesn't have enough privileges"
    #     )
    return current_user
