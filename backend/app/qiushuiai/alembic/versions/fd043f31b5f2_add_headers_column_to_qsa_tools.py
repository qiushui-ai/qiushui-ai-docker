"""add headers column to qsa_tools

Revision ID: fd043f31b5f2
Revises: b9844cceb639
Create Date: 2025-11-07 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "fd043f31b5f2"
down_revision = "b9844cceb639"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "qsa_tools",
        sa.Column(
            "headers",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.alter_column("qsa_tools", "headers", server_default=None)


def downgrade() -> None:
    op.drop_column("qsa_tools", "headers")

