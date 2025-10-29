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
down_revision = '606fbee1b0f2'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 tags 列到 qsa_sys_tags 表
    op.add_column('qsa_sys_tags', sa.Column('tags', postgresql.JSON(), nullable=True))


def downgrade():
    # 删除 tags 列
    op.drop_column('qsa_sys_tags', 'tags')
