from typing import Any
from qiushuiai.core import security
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from datetime import datetime
import uuid as uuid_module
from qiushuiai.core.config import settings

from fastapi import APIRouter, Body, HTTPException, Depends
from sqlmodel import func, select

from typing import Annotated, Any
from qiushuiai.schemas.user import Token
import logging  # 添加这行导入

# 在文件开头设置日志
logger = logging.getLogger(__name__)

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
from qiushuiai.core.security import get_password_hash, verify_password
from qiushuiai.schemas.user import (
    UsrUser,
    UsrUserCreate,
    UsrUserPublic,
    UsrUserUpdate,
    UsrUserUpdateMe,
    UsrUserUpdatePassword,
    UsrUserRegister,
)

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/page", response_model=BaseResponse[PageResponse[UsrUserPublic]])
def page_users(
    session: SessionDep, 
    current_user: CurrentUser, 
    request_data: Annotated[dict, Body(...)]
) -> Any:
    """获取用户列表。"""
    # 提取参数，设置默认值
    page = request_data.get("page", 1)
    rows = request_data.get("rows", 20)
    keyword = request_data.get("keyword")
    
    # 构建基础查询
    statement = select(UsrUser)
    
    # 应用通用过滤条件
    statement = apply_common_filters(
        statement=statement,
        model=UsrUser,
        current_user=current_user
    )
    
    # 应用关键词搜索
    statement = apply_keyword_search(
        statement=statement,
        model=UsrUser,
        keyword=keyword,
        search_fields=["username", "email", "first_name", "last_name"]
    )
    
    # 构建计数查询
    count_statement = get_count_query(statement, UsrUser)
    count = session.exec(count_statement).one()
    
    # 添加排序
    statement = build_order_by(
        statement=statement,
        model=UsrUser,
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
    users = session.exec(statement).all()
    
    # 使用标准分页响应格式
    return page_response(
        items=users,
        page=page,
        size=rows,
        total=count,
        message="获取用户列表成功"
    )


@router.post("/detail/{uuid}", response_model=BaseResponse[UsrUserPublic])
def read_user(
    session: SessionDep, 
    current_user: CurrentUser, 
    uuid: uuid_module.UUID
) -> Any:
    """根据UUID获取单个用户。"""
    statement = select(UsrUser).where(UsrUser.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=UsrUser,
        current_user=current_user
    )
    user = session.exec(statement).first()
    
    if not user:
        raise ResourceNotFoundException(message="用户不存在")
    
    return success_response(data=user, message="获取用户详情成功")


@router.post("/create", response_model=BaseResponse[UsrUserPublic])
def create_user(
    *, 
    session: SessionDep, 
    current_user: CurrentUser, 
    user_in: UsrUserCreate
) -> Any:
    """创建新用户。"""
    # 检查用户名是否已存在
    existing_user = session.exec(
        select(UsrUser).where(
            UsrUser.username == user_in.username,
            UsrUser.is_del == False
        )
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    existing_email = session.exec(
        select(UsrUser).where(
            UsrUser.email == user_in.email,
            UsrUser.is_del == False
        )
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="邮箱已存在"
        )
    
    user_data = user_in.model_dump()
    # 密码哈希处理
    user_data["password"] = get_password_hash(user_data["password"])

    
    # 使用通用函数更新公共字段
    user_data = update_common_fields(
        data=user_data,
        current_user=current_user,
        is_create=True
    )
    
    user = UsrUser.model_validate(user_data)
    session.add(user)
    session.commit()
    session.refresh(user)
    return success_response(
        data=user, 
        message=ResponseMessage.CREATED,
        code=ResponseCode.CREATED
    )


@router.post("/register", response_model=BaseResponse[UsrUserPublic])
def register_user(
    *, 
    session: SessionDep, 
    user_in: UsrUserRegister
) -> Any:
    """用户注册。"""
    # 检查用户名是否已存在
    existing_user = session.exec(
        select(UsrUser).where(
            UsrUser.username == user_in.username,
            UsrUser.is_del == False
        )
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    existing_email = session.exec(
        select(UsrUser).where(
            UsrUser.email == user_in.email,
            UsrUser.is_del == False
        )
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="邮箱已存在"
        )
    
    user_data = user_in.model_dump()
    # 密码哈希处理
    user_data["password"] = get_password_hash(user_data["password"])

    
    # 注册时设置基本字段，不需要current_user
    now = datetime.now()
    user_data.update({
        "created_at": now,
        "updated_at": now,
    })
    
    user = UsrUser.model_validate(user_data)
    session.add(user)
    session.commit()
    session.refresh(user)
    return success_response(
        data=user, 
        message="用户注册成功",
        code=ResponseCode.CREATED
    )


@router.put("/update/{uuid}", response_model=BaseResponse[UsrUserPublic])
def update_user(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    uuid: uuid_module.UUID,
    user_in: UsrUserUpdate,
) -> Any:
    """更新用户信息。"""
    statement = select(UsrUser).where(UsrUser.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=UsrUser,
        current_user=current_user
    )
    user = session.exec(statement).first()
    
    if not user:
        raise ResourceNotFoundException(message="用户不存在")
    
    update_dict = user_in.model_dump(exclude_unset=True)
    
    # 如果更新用户名，检查是否重复
    if "username" in update_dict and update_dict["username"] != user.username:
        existing_user = session.exec(
            select(UsrUser).where(
                UsrUser.username == update_dict["username"],
                UsrUser.is_del == False,
                UsrUser.id != user.id
            )
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="用户名已存在"
            )
    
    # 如果更新邮箱，检查是否重复
    if "email" in update_dict and update_dict["email"] != user.email:
        existing_email = session.exec(
            select(UsrUser).where(
                UsrUser.email == update_dict["email"],
                UsrUser.is_del == False,
                UsrUser.id != user.id
            )
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="邮箱已存在"
            )
    
    # 使用通用函数更新公共字段
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )
    
    user.sqlmodel_update(update_dict)
    session.add(user)
    session.commit()
    session.refresh(user)
    return success_response(data=user, message=ResponseMessage.UPDATED)


@router.patch("/password", response_model=BaseResponse[None])
def update_password(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    password_in: UsrUserUpdatePassword,
) -> Any:
    """用户修改密码。"""
    # 查找当前用户
    statement = select(UsrUser).where(UsrUser.id == current_user.id)
    user = session.exec(statement).first()
    
    if not user:
        raise ResourceNotFoundException(message="用户不存在")
    
    # 验证当前密码
    if not verify_password(password_in.current_password, user.password):
        raise HTTPException(
            status_code=400,
            detail="当前密码错误"
        )
    
    # 更新密码
    update_dict = {
        "password": get_password_hash(password_in.new_password)
    }
    
    # 使用通用函数更新公共字段
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )
    
    user.sqlmodel_update(update_dict)
    session.add(user)
    session.commit()
    return success_response(data=None, message="密码修改成功")


@router.delete("/delete/{uuid}", response_model=BaseResponse[None])
def delete_user(
    session: SessionDep, 
    current_user: CurrentUser, 
    uuid: uuid_module.UUID
) -> Any:
    """删除用户（软删除）。"""
    statement = select(UsrUser).where(UsrUser.uuid == uuid)
    statement = apply_common_filters(
        statement=statement,
        model=UsrUser,
        current_user=current_user
    )
    user = session.exec(statement).first()
    
    if not user:
        raise ResourceNotFoundException(message="用户不存在")
    
    # 执行软删除
    delete_data = {"is_del": True}
    delete_data = update_common_fields(
        data=delete_data,
        current_user=current_user,
        is_create=False
    )
    
    user.sqlmodel_update(delete_data)
    session.add(user)
    session.commit()
    return success_response(data=None, message=ResponseMessage.DELETED) 


@router.post("/login/access-token", response_model=BaseResponse[Token])
def login_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Any:
    """
    OAuth2 兼容的令牌登录，获取用于后续请求的访问令牌
    """
    # 使用用户名和密码验证登录

    statement = select(UsrUser).where(UsrUser.username == form_data.username)
    user = session.exec(statement).first()

    logger.info(f"登录调试 - 用户名: {form_data.username}")
    logger.info(f"登录调试 - 用户输入的明文密码: {form_data.password}")
    logger.info(f"登录调试 - 用户输入的哈希密码: {get_password_hash(form_data.password)}")
    
    if not user:
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户未激活")
    
    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="用户名或密码错误") 

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires, tenant_id=user.tenant_id
        )
    )
    
    return success_response(data=token_data, message="登录成功")



# def generate_password_reset_token(email: str) -> str:
#     delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
#     now = datetime.now(timezone.utc)
#     expires = now + delta
#     exp = expires.timestamp()
#     encoded_jwt = jwt.encode(
#         {"exp": exp, "nbf": now, "sub": email},
#         settings.SECRET_KEY,
#         algorithm=security.ALGORITHM,
#     )
#     return encoded_jwt


# def verify_password_reset_token(token: str) -> str | None:
#     try:
#         decoded_token = jwt.decode(
#             token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
#         )
#         return str(decoded_token["sub"])
#     except InvalidTokenError:
#         return None


@router.post("/me/update", response_model=BaseResponse[UsrUserPublic])
def update_user_me(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_in: UsrUserUpdateMe = Body(...)
) -> Any:
    """用户更新自己的信息。"""
    # 检查邮箱是否重复
    if user_in.email:
        existing_user = session.exec(
            select(UsrUser).where(
                UsrUser.email == user_in.email,
                UsrUser.is_del == False,
                UsrUser.id != current_user.id
            )
        ).first()
        if existing_user:
            raise HTTPException(status_code=409, detail="该邮箱已被其他用户占用")
    update_dict = user_in.model_dump(exclude_unset=True)
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )
    current_user.sqlmodel_update(update_dict)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return success_response(data=current_user, message="个人信息更新成功")


@router.post("/me/update-password", response_model=BaseResponse[None])
def update_password_me(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    password_in: UsrUserUpdatePassword = Body(...)
) -> Any:
    """用户修改自己的密码。"""
    if not verify_password(password_in.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="当前密码错误")
    if password_in.current_password == password_in.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与当前密码相同")
    update_dict = {
        "password": get_password_hash(password_in.new_password)
    }
    update_dict = update_common_fields(
        data=update_dict,
        current_user=current_user,
        is_create=False
    )
    current_user.sqlmodel_update(update_dict)
    session.add(current_user)
    session.commit()
    return success_response(data=None, message="密码修改成功")


@router.get("/me/detail", response_model=BaseResponse[UsrUserPublic])
def read_user_me(
    current_user: CurrentUser
) -> Any:
    """获取当前用户信息。"""
    return success_response(data=current_user, message="获取当前用户信息成功")


@router.post("/signup", response_model=BaseResponse[UsrUserPublic])
def register_user(
    session: SessionDep,
    user_in: UsrUserRegister = Body(...)
) -> Any:
    """注册新用户（无需登录）。"""
    # 检查邮箱是否已存在
    existing_user = session.exec(
        select(UsrUser).where(
            UsrUser.email == user_in.email,
            UsrUser.is_del == False
        )
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="该邮箱已被注册"
        )
    # 检查用户名是否已存在
    existing_username = session.exec(
        select(UsrUser).where(
            UsrUser.username == user_in.username,
            UsrUser.is_del == False
        )
    ).first()
    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="用户名已存在"
        )
    user_data = user_in.model_dump()
    user_data["password"] = get_password_hash(user_data["password"])
 
    now = datetime.now()
    user_data.update({
        "created_at": now,
        "updated_at": now,
    })
    user = UsrUser.model_validate(user_data)
    session.add(user)
    session.commit()
    session.refresh(user)
    return success_response(data=user, message="注册成功", code=ResponseCode.CREATED)