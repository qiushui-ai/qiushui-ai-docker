from sqlmodel import Session, create_engine, select

from qiushuiai.core.config import settings

engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    # echo=settings.ENVIRONMENT == "local"  # 在本地环境启用 SQL 日志
)


# 确保在初始化数据库之前导入所有 SQLModel 模型 (app.models)
# 否则, SQLModel 可能无法正确初始化关系
# 更多详情请参考: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # 数据表应该通过 Alembic 迁移创建
    # 但如果你不想使用迁移，可以取消注释以下代码来创建表
    # from sqlmodel import SQLModel

    # 这段代码可以工作是因为模型已经从 qiushuiai.models 导入并注册
    # SQLModel.metadata.create_all(engine)
    
    # 创建初始管理员用户
    from qiushuiai.schemas.user import UsrUser
    from qiushuiai.core import security

    # 从环境变量获取超级用户信息
    first_superuser_username = settings.FIRST_FIRST_SUPER_USERNAME
    first_superuser_email = settings.FIRST_SUPERUSER_EMAIL
    first_superuser_password = settings.FIRST_SUPERUSER_PASSWORD
    first_superuser_phone = settings.FIRST_SUPERUSER_PHONE
    api_key = settings.API_KEY

    # 检查初始管理员用户是否存在
    superuser = session.exec(
        select(UsrUser).where(UsrUser.email == first_superuser_email)
    ).first()

    if not superuser:
        # 创建初始管理员用户
        hashed_password = security.get_password_hash(first_superuser_password)
        superuser = UsrUser(
            username=first_superuser_username,
            email=first_superuser_email,
            password=hashed_password,
            phone_number=first_superuser_phone,
            role="admin",
            is_active=True,
            is_email_verified=True,
            is_phone_verified=bool(first_superuser_phone),  # 如果提供了手机号则设为已验证
            tenant_id=1,  # 默认租户ID
            login_count=0,
            api_key=api_key if api_key else None,  # 设置API密钥
        )
        session.add(superuser)
        session.commit()
        session.refresh(superuser)
        print(f"✅ 初始管理员用户已创建:")
        print(f"   用户名: {first_superuser_username}")
        print(f"   邮箱: {first_superuser_email}")
        print(f"   密码: {first_superuser_password}")
        print(f"   手机: {first_superuser_phone or '未设置'}")
        if api_key:
            print(f"✅ API密钥已设置: {api_key[:10]}...")