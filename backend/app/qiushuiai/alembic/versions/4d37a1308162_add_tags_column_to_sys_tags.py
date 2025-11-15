"""add_tags_column_to_sys_tags

Revision ID: 4d37a1308162
Revises: 606fbee1b0f2
Create Date: 2025-08-03 11:03:16.794335

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '4d37a1308162'
down_revision = 'add_tags_column_to_agent'
branch_labels = None
depends_on = None


def upgrade():
    # 注意：此迁移已被初始迁移(73e7fc808773)包含
    # tags 字段已在初始表创建时添加
    # 此迁移保留用于历史记录兼容性，不执行任何操作
    pass


def downgrade():
    # 此迁移不执行任何操作，因此降级也不需要操作
    pass
