"""Add tool_info jsonb field to qsa_tools table

Revision ID: 44db85b9c11e
Revises: fd043f31b5f2
Create Date: 2025-11-15 15:58:24.588989

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '44db85b9c11e'
down_revision = 'fd043f31b5f2'
branch_labels = None
depends_on = None


def upgrade():
    # Add tool_info jsonb field to qsa_tools table
    op.add_column('qsa_tools', sa.Column('tool_info', sa.JSON(), nullable=True))


def downgrade():
    # Remove tool_info field from qsa_tools table
    op.drop_column('qsa_tools', 'tool_info')
