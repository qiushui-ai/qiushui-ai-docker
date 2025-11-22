"""Add qsa_note_collect_content table and remove content fields from qsa_note_collect

Revision ID: dd1eb32dfa0b
Revises: 98c636f279e8
Create Date: 2025-11-22 10:45:24.150548

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dd1eb32dfa0b'
down_revision = '98c636f279e8'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: 创建新的内容表
    op.create_table('qsa_note_collect_content',
    sa.Column('cn_content', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('en_content', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('extdata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
    sa.Column('uuid', sa.Uuid(), nullable=False),
    sa.Column('collect_uuid', sa.Uuid(), nullable=False),
    sa.Column('tenant_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('updated_by', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('uuid')
    )

    # Step 2: 添加外键约束
    op.create_foreign_key(
        'fk_collect_content_collect_uuid',
        'qsa_note_collect_content',
        'qsa_note_collect',
        ['collect_uuid'],
        ['uuid'],
        ondelete='CASCADE'
    )

    # Step 3: 创建索引
    op.create_index('ix_note_collect_content_collect_uuid', 'qsa_note_collect_content', ['collect_uuid'])

    # Step 4: 迁移现有数据
    op.execute("""
        INSERT INTO qsa_note_collect_content (
            uuid, collect_uuid, cn_content, en_content, extdata,
            tenant_id, created_by, updated_by, created_at, updated_at
        )
        SELECT
            gen_random_uuid(), uuid, cn_content, en_content, extdata,
            tenant_id, created_by, updated_by, created_at, updated_at
        FROM qsa_note_collect
        WHERE cn_content IS NOT NULL OR en_content IS NOT NULL OR extdata IS NOT NULL
    """)

    # Step 5: 删除原表的字段
    op.drop_column('qsa_note_collect', 'extdata')
    op.drop_column('qsa_note_collect', 'en_content')
    op.drop_column('qsa_note_collect', 'cn_content')


def downgrade():
    # Step 1: 添加回原来的字段
    op.add_column('qsa_note_collect', sa.Column('cn_content', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('qsa_note_collect', sa.Column('en_content', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('qsa_note_collect', sa.Column('extdata', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))

    # Step 2: 迁移数据回主表
    op.execute("""
        UPDATE qsa_note_collect
        SET
            cn_content = qncc.cn_content,
            en_content = qncc.en_content,
            extdata = qncc.extdata
        FROM qsa_note_collect_content qncc
        WHERE qsa_note_collect.uuid = qncc.collect_uuid
    """)

    # Step 3: 删除内容表
    op.drop_table('qsa_note_collect_content')
