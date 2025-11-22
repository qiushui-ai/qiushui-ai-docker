#!/usr/bin/env python
"""
修复用户表中缺失的时间戳字段
"""

from datetime import datetime
from sqlmodel import Session, select, update
from qiushuiai.core.db import engine
from qiushuiai.schemas.user import UsrUser


def fix_user_timestamps():
    """修复用户表中的时间戳字段"""
    with Session(engine) as session:
        print("🔍 检查用户表中的时间戳字段...")

        # 查询 created_at 或 updated_at 为 NULL 的用户
        stmt = select(UsrUser).where(
            (UsrUser.created_at.is_(None)) | (UsrUser.updated_at.is_(None))
        )
        users_to_fix = session.exec(stmt).all()

        if not users_to_fix:
            print("✅ 所有用户记录的时间戳字段都正常")
            return

        print(f"🛠️  发现 {len(users_to_fix)} 个用户记录需要修复")

        current_time = datetime.now()
        fixed_count = 0

        for user in users_to_fix:
            updated = False

            if user.created_at is None:
                user.created_at = current_time
                updated = True
                print(f"  - 修复用户 {user.username} 的 created_at")

            if user.updated_at is None:
                user.updated_at = current_time
                updated = True
                print(f"  - 修复用户 {user.username} 的 updated_at")

            if updated:
                session.add(user)
                fixed_count += 1

        # 提交更改
        session.commit()
        print(f"✅ 成功修复 {fixed_count} 个用户记录的时间戳")


def main():
    """主函数"""
    print("=" * 50)
    print("用户时间戳修复工具")
    print("=" * 50)

    try:
        fix_user_timestamps()
        print("🎉 修复完成！")
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        raise


if __name__ == "__main__":
    main()