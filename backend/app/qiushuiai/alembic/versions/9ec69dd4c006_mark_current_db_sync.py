"""mark_current_db_sync

Revision ID: 9ec69dd4c006
Revises: fix_whiteboard_is_public_type
Create Date: 2025-10-28 11:37:34.828079

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '9ec69dd4c006'
down_revision = 'fix_whiteboard_is_public_type'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
