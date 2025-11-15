import uuid as uuid_module
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, JSON, Column
from sqlalchemy import TIMESTAMP, Identity
from pydantic import BaseModel, EmailStr


# 除了id、uuid、tenant_id、is_del、created_at、created_by、updated_at、updated_by之外的属性
# 属性定义与数据库模型一致
class UsrUserBase(SQLModel):
    username: str = Field(max_length=150, description="用户名")
    email: EmailStr = Field(max_length=254, description="邮箱地址")
    first_name: str | None = Field(default=None, max_length=100, description="名")
    last_name: str | None = Field(default=None, max_length=100, description="姓")
    avatar: str | None = Field(default=None, description="头像URL")
    phone_number: str | None = Field(default=None, max_length=20, description="手机号码")
    is_active: bool = Field(default=True, description="是否激活")
    is_email_verified: bool = Field(default=False, description="邮箱是否验证")
    is_phone_verified: bool = Field(default=False, description="手机是否验证")
    role: str = Field(default="member", max_length=20, description="角色(owner/admin/member)")
    last_login: datetime | None = Field(default=None, description="最后登录时间")
    login_count: int = Field(default=0, description="登录次数")
    preferences: dict = Field(default_factory=dict, sa_column=Column(JSON), description="用户偏好设置")


# 创建时的模型，包含密码字段
class UsrUserCreate(UsrUserBase):
    password: str = Field(min_length=8, max_length=128, description="密码")
    
    
# 用户注册模型（简化版）
class UsrUserRegister(SQLModel):
    username: str = Field(max_length=150, description="用户名")
    email: EmailStr | None = Field(default=None, max_length=254, description="邮箱地址")
    password: str = Field(min_length=8, max_length=128, description="密码")
    first_name: str | None = Field(default=None, max_length=100, description="名")
    last_name: str | None = Field(default=None, max_length=100, description="姓")


# 除了id、uuid、tenant_id、is_del、created_at、created_by、updated_at、updated_by之外的属性
# 属性都可为None
class UsrUserUpdate(SQLModel):
    username: str | None = Field(default=None, max_length=150, description="用户名")
    email: EmailStr | None = Field(default=None, max_length=254, description="邮箱地址")
    first_name: str | None = Field(default=None, max_length=100, description="名")
    last_name: str | None = Field(default=None, max_length=100, description="姓")
    avatar: str | None = Field(default=None, description="头像URL")
    phone_number: str | None = Field(default=None, max_length=20, description="手机号码")
    is_active: bool | None = Field(default=None, description="是否激活")
    is_email_verified: bool | None = Field(default=None, description="邮箱是否验证")
    is_phone_verified: bool | None = Field(default=None, description="手机是否验证")
    role: str | None = Field(default=None, max_length=20, description="角色(owner/admin/member)")
    preferences: dict | None = Field(default=None, description="用户偏好设置")


# 用户自己更新信息的模型（限制部分字段）
class UsrUserUpdateMe(SQLModel):
    first_name: str | None = Field(default=None, max_length=100, description="名")
    last_name: str | None = Field(default=None, max_length=100, description="姓")
    avatar: str | None = Field(default=None, description="头像URL")
    phone_number: str | None = Field(default=None, max_length=20, description="手机号码")
    preferences: dict | None = Field(default=None, description="用户偏好设置")


# 修改密码模型
class UsrUserUpdatePassword(SQLModel):
    current_password: str = Field(min_length=1, description="当前密码")
    new_password: str = Field(min_length=8, max_length=128, description="新密码")


# 数据库模型 - 表名为qsa_usr_user
# 包含id、uuid、tenant_id、is_del、created_at、created_by、updated_at、updated_by字段
class UsrUser(UsrUserBase, table=True):
    __tablename__ = "qsa_usr_user"
    
    # 系统字段
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"server_default": Identity()})
    uuid: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, unique=True, description="用户UUID")
    tenant_id: int = Field(description="所属租户ID")
    password: str = Field(max_length=128, description="密码哈希")
    is_del: bool = Field(default=False, description="是否删除")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="创建时间")
    created_by: int | None = Field(default=None, description="创建者")
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(TIMESTAMP(timezone=True)), description="更新时间")
    updated_by: int | None = Field(default=None, description="最后修改者")


# 列表或者详情返回的属性
class UsrUserPublic(UsrUserBase):
    id: int
    uuid: uuid_module.UUID
    tenant_id: int
    is_del: bool
    created_at: datetime
    created_by: int | None
    updated_at: datetime
    updated_by: int | None

# 包含访问令牌的JSON负载
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# JWT令牌的内容
class TokenPayload(SQLModel):
    sub: str | None = None
    tenant_id: int | None = None