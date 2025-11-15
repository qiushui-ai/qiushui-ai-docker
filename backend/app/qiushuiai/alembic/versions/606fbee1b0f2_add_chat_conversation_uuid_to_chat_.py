"""add chat_conversation_uuid to chat_document table

Revision ID: 606fbee1b0f2
Revises: 
Create Date: 2025-08-01 22:23:33.917186

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '606fbee1b0f2'
down_revision = '73e7fc808773'
branch_labels = None
depends_on = None


def upgrade():
    # 注意：此迁移已被初始迁移(73e7fc808773)包含
    # chat_conversation_uuid 字段已在初始表创建时添加
    # 此迁移保留用于历史记录兼容性，不执行任何操作
    pass


def downgrade():
    # 此迁移不执行任何操作，因此降级也不需要操作
    pass
