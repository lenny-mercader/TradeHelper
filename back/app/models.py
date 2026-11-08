import datetime as dt
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

PRICE = Numeric(18, 6)


class Base(DeclarativeBase):
    pass


class Instrument(Base):
    """Any stock/ETF the app knows: the US catalog (Massive) plus whatever was opened via Yahoo.

    `symbol` uses Yahoo's format everywhere (AAPL, BRK-B, MC.PA, 7203.T).
    `currency` is the major unit (GBP, not GBp): prices are normalised when stored.
    """

    __tablename__ = "instruments"

    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(256))
    exchange: Mapped[str | None] = mapped_column(String(64))
    currency: Mapped[str | None] = mapped_column(String(8))
    type: Mapped[str | None] = mapped_column(String(16))
    # Listed in the Massive US catalog (covered by the daily grouped snapshot).
    is_us: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    history_loaded_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    # Last day an update was attempted (at most one provider call per day per symbol).
    # Non-null means the instrument has been opened at least once: the nightly job keeps it fresh.
    history_checked_on: Mapped[dt.date | None] = mapped_column(Date)


class WatchlistItem(Base):
    """One symbol in one user's watchlist. `user_id` is the Clerk user id (no local user table)."""

    __tablename__ = "watchlist_items"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    symbol: Mapped[str] = mapped_column(
        String(32), ForeignKey("instruments.symbol", ondelete="CASCADE"), primary_key=True
    )
    added_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DailyPrice(Base):
    """End-of-day bar in the instrument's currency, split-adjusted (not dividend-adjusted).

    Yahoo only serves split-adjusted closes, so a split triggers a full reload of the history.
    """

    __tablename__ = "daily_prices"

    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    open: Mapped[Decimal] = mapped_column(PRICE)
    high: Mapped[Decimal] = mapped_column(PRICE)
    low: Mapped[Decimal] = mapped_column(PRICE)
    close: Mapped[Decimal] = mapped_column(PRICE)
    volume: Mapped[int] = mapped_column(BigInteger)


class UsSnapshot(Base):
    """Latest end-of-day bar of every US ticker (one Massive grouped call), replaced daily."""

    __tablename__ = "us_snapshot"

    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date)
    open: Mapped[Decimal] = mapped_column(PRICE)
    high: Mapped[Decimal] = mapped_column(PRICE)
    low: Mapped[Decimal] = mapped_column(PRICE)
    close: Mapped[Decimal] = mapped_column(PRICE)
    volume: Mapped[int] = mapped_column(BigInteger)
    prev_close: Mapped[Decimal | None] = mapped_column(PRICE)
    # Split executed since the previous session: close vs prev_close is meaningless.
    split: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class FxRate(Base):
    """Units of `currency` for 1 EUR on `date` (ECB reference rate, Yahoo as fallback)."""

    __tablename__ = "fx_rates"

    currency: Mapped[str] = mapped_column(String(8), primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(20, 8))
