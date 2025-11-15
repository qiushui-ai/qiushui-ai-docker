"""convert_parent_id_to_uuid_in_note_tag

Revision ID: b9844cceb639
Revises: d6ff6152f601
Create Date: 2025-11-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'b9844cceb639'
down_revision = 'd6ff6152f601'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 添加新的 parent_uuid 列（临时列）
    op.add_column('qsa_note_tag', sa.Column('parent_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    
    # 2. 将现有的 parent_id（整数）转换为 parent_uuid（UUID）
    # 通过 JOIN 查询找到父标签的 uuid
    op.execute("""
        UPDATE qsa_note_tag child
        SET parent_uuid = parent.uuid
        FROM qsa_note_tag parent
        WHERE child.parent_id = parent.id
    """)
    
    # 3. 删除旧的 parent_id 列
    op.drop_column('qsa_note_tag', 'parent_id')
    
    # 4. 将 parent_uuid 重命名为 parent_id
    op.alter_column('qsa_note_tag', 'parent_uuid', new_column_name='parent_id')


def downgrade():
    # 1. 添加新的 parent_id 列（整数类型，临时列）
    op.add_column('qsa_note_tag', sa.Column('parent_id_new', sa.Integer(), nullable=True))
    
    # 2. 将 parent_id（UUID）转换为 parent_id_new（整数）
    # 通过 JOIN 查询找到父标签的 id
    op.execute("""
        UPDATE qsa_note_tag child
        SET parent_id_new = parent.id
        FROM qsa_note_tag parent
        WHERE child.parent_id = parent.uuid
    """)
    
    # 3. 删除旧的 parent_id 列（UUID类型）
    op.drop_column('qsa_note_tag', 'parent_id')
    
    # 4. 将 parent_id_new 重命名为 parent_id
    op.alter_column('qsa_note_tag', 'parent_id_new', new_column_name='parent_id')

