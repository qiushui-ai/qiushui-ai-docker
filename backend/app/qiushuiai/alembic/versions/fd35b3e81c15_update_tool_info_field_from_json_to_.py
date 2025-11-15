"""Update tool_info field from JSON to JSONB

Revision ID: fd35b3e81c15
Revises: 44db85b9c11e
Create Date: 2025-11-15 16:33:55.358006

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'fd35b3e81c15'
down_revision = '44db85b9c11e'
branch_labels = None
depends_on = None


def upgrade():
    # Update tool_info field from JSON to JSONB
    op.alter_column('qsa_tools', 'tool_info',
               existing_type=sa.JSON(),
               type_=sa.dialects.postgresql.JSONB(),
               existing_nullable=True)


def downgrade():
    # Revert tool_info field from JSONB to JSON
    op.alter_column('qsa_tools', 'tool_info',
               existing_type=sa.dialects.postgresql.JSONB(),
               type_=sa.JSON(),
               existing_nullable=True)
