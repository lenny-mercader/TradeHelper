"""instrument profile (Yahoo fundamentals) + daily transaction count

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("instruments", sa.Column("profile", postgresql.JSONB()))
    op.add_column("instruments", sa.Column("profile_loaded_at", sa.DateTime(timezone=True)))
    op.add_column("us_snapshot", sa.Column("transactions", sa.BigInteger()))


def downgrade() -> None:
    op.drop_column("us_snapshot", "transactions")
    op.drop_column("instruments", "profile_loaded_at")
    op.drop_column("instruments", "profile")
