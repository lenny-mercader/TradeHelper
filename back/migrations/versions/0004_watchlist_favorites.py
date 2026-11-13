"""favorite flag on watchlist items

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "watchlist_items",
        sa.Column("favorite", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("watchlist_items", sa.Column("favorited_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column("watchlist_items", "favorited_at")
    op.drop_column("watchlist_items", "favorite")
