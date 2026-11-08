"""instruments catalog, US snapshot, FX rates

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-08
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

PRICE = sa.Numeric(18, 6)


def upgrade() -> None:
    op.create_table(
        "instruments",
        sa.Column("symbol", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(256)),
        sa.Column("exchange", sa.String(64)),
        sa.Column("currency", sa.String(8)),
        sa.Column("type", sa.String(16)),
        sa.Column("is_us", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("followed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("history_loaded_at", sa.DateTime(timezone=True)),
        sa.Column("history_checked_on", sa.Date()),
    )
    op.create_index("ix_instruments_followed", "instruments", ["followed"])

    op.create_table(
        "us_snapshot",
        sa.Column("symbol", sa.String(32), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("open", PRICE, nullable=False),
        sa.Column("high", PRICE, nullable=False),
        sa.Column("low", PRICE, nullable=False),
        sa.Column("close", PRICE, nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("prev_close", PRICE),
        sa.Column("split", sa.Boolean(), nullable=False, server_default="false"),
    )

    op.create_table(
        "fx_rates",
        sa.Column("currency", sa.String(8), primary_key=True),
        sa.Column("date", sa.Date(), primary_key=True),
        sa.Column("rate", sa.Numeric(20, 8), nullable=False),
    )

    op.alter_column("daily_prices", "symbol", type_=sa.String(32))
    for col in ("open", "high", "low", "close"):
        op.alter_column("daily_prices", col, type_=PRICE)

    # Symbols loaded by the previous fixed-list version become followed US instruments.
    # Their history (raw Tiingo prices) is marked as not loaded, so it gets reloaded
    # split-adjusted from Yahoo like every other instrument.
    op.execute(
        """
        INSERT INTO instruments (symbol, currency, is_us, followed)
        SELECT DISTINCT symbol, 'USD', true, true FROM daily_prices
        """
    )


def downgrade() -> None:
    for col in ("open", "high", "low", "close"):
        op.alter_column("daily_prices", col, type_=sa.Numeric(14, 4))
    op.alter_column("daily_prices", "symbol", type_=sa.String(16))
    op.drop_table("fx_rates")
    op.drop_table("us_snapshot")
    op.drop_index("ix_instruments_followed", "instruments")
    op.drop_table("instruments")
