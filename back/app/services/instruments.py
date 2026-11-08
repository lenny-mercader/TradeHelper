"""Instruments are loaded on demand: full history the first time, then at most one update per day."""

import datetime as dt
import re

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import DailyPrice, Instrument
from app.providers import yahoo
from app.providers.common import Bar, NotFoundError, ProviderError
from app.providers.massive import MassiveClient
from app.services import fx
from app.services.upsert import PRICE_COLUMNS, upsert

SYMBOL_RE = re.compile(r"^[A-Z0-9.\-^=&]{1,32}$")

# Massive free tier serves 2 years of daily history.
MASSIVE_HISTORY = dt.timedelta(days=730)


class InvalidSymbolError(ValueError):
    pass


def normalize_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if not SYMBOL_RE.match(symbol):
        raise InvalidSymbolError(symbol)
    return symbol


def save_bars(session: Session, bars: list[Bar]) -> None:
    upsert(session, DailyPrice, bars, ("symbol", "date"), PRICE_COLUMNS)


def _fetch(
    instrument: Instrument | None, symbol: str, start: dt.date, settings: Settings
) -> tuple[list[Bar], yahoo.History | None]:
    """Yahoo first (worldwide, 5 years); Massive as fallback for US-listed symbols."""
    try:
        history = yahoo.fetch_history(symbol, start)
        return history.bars, history
    except ProviderError as yahoo_error:
        if not (instrument and instrument.is_us):
            raise
        today = dt.date.today()
        massive_start = max(start, today - MASSIVE_HISTORY)
        try:
            with MassiveClient(settings.massive_api_key) as massive:
                return massive.daily_range(symbol, massive_start, today), None
        except ProviderError:
            raise yahoo_error from None


def ensure_loaded(session: Session, settings: Settings, symbol: str) -> Instrument:
    """Return the instrument with its history loaded and updated today.

    Raises NotFoundError for unknown symbols and ProviderError when every source failed
    (only if nothing is stored yet: stale data is better than no data).
    """
    symbol = normalize_symbol(symbol)
    instrument = session.get(Instrument, symbol)
    today = dt.date.today()

    if instrument and instrument.history_loaded_at and instrument.history_checked_on == today:
        return instrument

    full_start = today - dt.timedelta(days=365 * settings.history_years)
    last = session.scalar(select(func.max(DailyPrice.date)).where(DailyPrice.symbol == symbol))
    full = instrument is None or instrument.history_loaded_at is None or last is None
    start = full_start if full else last

    try:
        bars, meta = _fetch(instrument, symbol, start, settings)
        if not full and meta and meta.split_after_start:
            # Split since the last update: stored bars are on the old scale, reload everything.
            full = True
            bars, meta = _fetch(instrument, symbol, full_start, settings)
    except ProviderError:
        if instrument and instrument.history_loaded_at:
            instrument.history_checked_on = today
            session.commit()
            return instrument
        raise

    if instrument is None:
        instrument = Instrument(symbol=symbol)
        session.add(instrument)
    if meta:
        instrument.name = instrument.name or meta.name
        instrument.exchange = instrument.exchange or meta.exchange
        instrument.type = instrument.type or meta.type
        instrument.currency = meta.currency or instrument.currency
    if instrument.is_us and not instrument.currency:
        instrument.currency = "USD"
    if full:
        instrument.history_loaded_at = dt.datetime.now(dt.UTC)
        # Drop the previous history: it may be on another price scale or cover another range.
        session.execute(delete(DailyPrice).where(DailyPrice.symbol == symbol))
    instrument.history_checked_on = today
    session.flush()

    save_bars(session, bars)
    session.commit()
    fx.ensure_currency(session, instrument.currency)
    return instrument


def history(session: Session, symbol: str) -> list[DailyPrice]:
    return list(
        session.scalars(
            select(DailyPrice).where(DailyPrice.symbol == symbol).order_by(DailyPrice.date)
        )
    )


def last_two(session: Session, symbol: str) -> list[DailyPrice]:
    return list(
        session.scalars(
            select(DailyPrice)
            .where(DailyPrice.symbol == symbol)
            .order_by(DailyPrice.date.desc())
            .limit(2)
        )
    )


__all__ = ["InvalidSymbolError", "NotFoundError", "ProviderError", "ensure_loaded"]
