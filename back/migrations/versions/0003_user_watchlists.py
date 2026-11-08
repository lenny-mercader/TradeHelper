"""per-user watchlists (Clerk user ids) replace the global followed flag

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-08
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "watchlist_items",
        sa.Column("user_id", sa.String(64), primary_key=True),
        sa.Column(
            "symbol",
            sa.String(32),
            sa.ForeignKey("instruments.symbol", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "added_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    # The previous global list is dropped on purpose: every account starts empty.
    op.drop_index("ix_instruments_followed", "instruments")
    op.drop_column("instruments", "followed")


def downgrade() -> None:
    op.add_column(
        "instruments",
        sa.Column("followed", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("ix_instruments_followed", "instruments", ["followed"])
    op.drop_table("watchlist_items")
