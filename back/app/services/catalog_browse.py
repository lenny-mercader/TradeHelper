"""Browsing/searching the known instruments: US catalog (full) + international (already opened).

Market cap and sector come from `Instrument.profile` (Yahoo, loaded lazily — see
services/instruments.py and the `profiles` backfill job), so they read "—" until populated.
"""

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import Float, case, func, select
from sqlalchemy.orm import Session

from app.models import DailyPrice, FxRate, Instrument, UsSnapshot
from app.services import fx

PAGE_SIZE = 50
# "Stock" types to include, ETFs excluded — vocabulary differs by source: Massive for the US
# catalog (CS, ADRC) vs. Yahoo for international instruments opened individually (EQUITY).
US_STOCK_TYPES = ("CS", "ADRC")
INTL_STOCK_TYPES = ("EQUITY",)

SECTOR = Instrument.profile["sector"].astext
COUNTRY = case((Instrument.is_us, "United States"), else_=Instrument.profile["country"].astext)

_MARKET_CAP_LOCAL = Instrument.profile["marketCap"].astext.cast(Float)
# A company's own currency, not the trading day: the latest known rate is accurate enough for a
# figure that is itself just a snapshot, and it lets this stay a cheap correlated subquery
# instead of joining a specific date. Mixing a Korean won market cap with a US-dollar one
# unconverted would otherwise make Samsung outrank Apple by raw digit count alone.
_LATEST_FX_RATE = (
    select(FxRate.rate)
    .where(FxRate.currency == Instrument.currency)
    .order_by(FxRate.date.desc())
    .limit(1)
    .correlate(Instrument)
    .scalar_subquery()
)
MARKET_CAP_EUR = case(
    (_MARKET_CAP_LOCAL.is_(None), None),
    (Instrument.currency == "EUR", _MARKET_CAP_LOCAL),
    else_=_MARKET_CAP_LOCAL / _LATEST_FX_RATE,
)

Sort = Literal["change", "market_cap", "name"]


@dataclass
class CatalogRow:
    symbol: str
    name: str | None
    country: str | None
    sector: str | None
    currency: str | None
    close: float | None  # EUR
    change_percent: float | None
    market_cap: float | None  # EUR


@dataclass
class CatalogPage:
    rows: list[CatalogRow]
    total: int


def _us_rows():
    """US rows via UsSnapshot: already has today's close/change for every catalog ticker,
    whether or not anyone has ever opened that instrument."""
    change = case(
        (UsSnapshot.prev_close > 0, (UsSnapshot.close - UsSnapshot.prev_close) / UsSnapshot.prev_close * 100),
        else_=None,
    )
    return (
        select(
            Instrument.symbol,
            Instrument.name,
            COUNTRY.label("country"),
            SECTOR.label("sector"),
            Instrument.currency,
            UsSnapshot.close.label("close_local"),
            UsSnapshot.date,
            change.label("change_percent"),
            MARKET_CAP_EUR.label("market_cap"),
        )
        .select_from(Instrument)
        .join(UsSnapshot, UsSnapshot.symbol == Instrument.symbol)
        .where(Instrument.is_us, Instrument.type.in_(US_STOCK_TYPES), UsSnapshot.split.is_(False))
    )


def _international_rows():
    """The handful of non-US instruments someone has opened: latest two DailyPrice rows give
    today's close/change, the same way the stock page itself does."""
    ranked = (
        select(
            DailyPrice.symbol,
            DailyPrice.date,
            DailyPrice.close,
            func.row_number()
            .over(partition_by=DailyPrice.symbol, order_by=DailyPrice.date.desc())
            .label("rank"),
        )
        .join(Instrument, Instrument.symbol == DailyPrice.symbol)
        .where(~Instrument.is_us, Instrument.type.in_(INTL_STOCK_TYPES))
        .subquery()
    )
    latest = ranked.alias("latest")
    previous = ranked.alias("previous")
    change = case(
        (previous.c.close > 0, (latest.c.close - previous.c.close) / previous.c.close * 100),
        else_=None,
    )
    return (
        select(
            Instrument.symbol,
            Instrument.name,
            COUNTRY.label("country"),
            SECTOR.label("sector"),
            Instrument.currency,
            latest.c.close.label("close_local"),
            latest.c.date,
            change.label("change_percent"),
            MARKET_CAP_EUR.label("market_cap"),
        )
        .select_from(Instrument)
        .join(latest, (latest.c.symbol == Instrument.symbol) & (latest.c.rank == 1))
        .outerjoin(previous, (previous.c.symbol == Instrument.symbol) & (previous.c.rank == 2))
    )


def search(
    session: Session,
    *,
    q: str | None = None,
    countries: list[str] | None = None,
    sector: str | None = None,
    min_change: float | None = None,
    max_change: float | None = None,
    sort: Sort = "market_cap",
    descending: bool = True,
    page: int = 1,
) -> CatalogPage:
    union = _us_rows().union_all(_international_rows()).subquery()
    stmt = select(union)

    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(union.c.symbol.ilike(pattern) | union.c.name.ilike(pattern))
    if countries:
        stmt = stmt.where(union.c.country.in_(countries))
    if sector:
        stmt = stmt.where(union.c.sector == sector)
    if min_change is not None:
        stmt = stmt.where(union.c.change_percent >= min_change)
    if max_change is not None:
        stmt = stmt.where(union.c.change_percent <= max_change)

    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    order_column = {
        "change": union.c.change_percent,
        "market_cap": union.c.market_cap,
        "name": union.c.name,
    }[sort]
    # NULLS LAST regardless of direction: unfilled market cap/sector shouldn't dominate the top.
    order = order_column.desc().nulls_last() if descending else order_column.asc().nulls_last()
    stmt = stmt.order_by(order, union.c.symbol).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)

    page_rows = session.execute(stmt).all()

    # EUR conversion, one Converter per currency present on this page (small, a handful at most).
    currencies = {r.currency for r in page_rows if r.currency}
    converters = {c: fx.Converter(session, c) for c in currencies}

    rows = [
        CatalogRow(
            symbol=r.symbol,
            name=r.name,
            country=r.country,
            sector=r.sector,
            currency=r.currency,
            close=converters[r.currency].to_eur(float(r.close_local), r.date)
            if r.currency and r.close_local is not None
            else None,
            change_percent=r.change_percent,
            market_cap=r.market_cap,
        )
        for r in page_rows
    ]
    return CatalogPage(rows=rows, total=total)


def facets(session: Session) -> dict[str, list[str]]:
    """Countries and sectors actually present, for the filter checkboxes/dropdown."""
    union = _us_rows().union_all(_international_rows()).subquery()
    countries = session.scalars(
        select(union.c.country).where(union.c.country.is_not(None)).distinct().order_by(union.c.country)
    ).all()
    sectors = session.scalars(
        select(union.c.sector)
        # A loaded-but-empty profile (failed fetch) can leave sector as "" rather than absent.
        .where(union.c.sector.is_not(None), union.c.sector != "")
        .distinct()
        .order_by(union.c.sector)
    ).all()
    return {"countries": list(countries), "sectors": list(sectors)}
