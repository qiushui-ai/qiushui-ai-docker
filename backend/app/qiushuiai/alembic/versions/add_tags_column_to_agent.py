"""add_tags_column_to_agent

Revision ID: add_tags_column_to_agent
Revises: 606fbee1b0f2
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_tags_column_to_agent'
down_revision = '606fbee1b0f2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 注意：此迁移已被初始迁移(73e7fc808773)包含
    # tags 字段已在初始表创建时添加
    # 此迁移保留用于历史记录兼容性，不执行任何操作
    pass


def downgrade() -> None:
    # 此迁移不执行任何操作，因此降级也不需要操作
    pass 