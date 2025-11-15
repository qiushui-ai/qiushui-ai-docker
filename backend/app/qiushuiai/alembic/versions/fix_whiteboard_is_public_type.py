"""fix whiteboard is_public field type

Revision ID: fix_whiteboard_is_public_type
Revises: add_tags_column_to_agent
Create Date: 2025-01-22 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_whiteboard_is_public_type'
down_revision = '4d37a1308162'
branch_labels = None
depends_on = None


def upgrade():
    # 注意：此迁移已被初始迁移(73e7fc808773)包含
    # 白板表的字段类型已在初始表创建时正确设置
    # 此迁移保留用于历史记录兼容性，不执行任何操作
    pass


def downgrade():
    # 此迁移不执行任何操作，因此降级也不需要操作
    pass
