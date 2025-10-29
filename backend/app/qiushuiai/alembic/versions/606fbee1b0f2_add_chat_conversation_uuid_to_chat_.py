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
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 添加 chat_conversation_uuid 字段
    op.add_column('qsa_chat_document', sa.Column('chat_conversation_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    
    # 确保 chat_conversation_id 字段可以为空（如果它还不是可空的）
    op.alter_column('qsa_chat_document', 'chat_conversation_id',
                    existing_type=sa.INTEGER(),
                    nullable=True)


def downgrade():
    # 删除 chat_conversation_uuid 字段
    op.drop_column('qsa_chat_document', 'chat_conversation_uuid')
    
    # 恢复 chat_conversation_id 字段为不可空（如果需要的话）
    # 注意：这可能会失败，如果表中已经有空值
    # op.alter_column('qsa_chat_document', 'chat_conversation_id',
    #                 existing_type=sa.INTEGER(),
    #                 nullable=False)
