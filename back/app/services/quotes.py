from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Instrument, WatchlistItem
from app.schemas import Quote
from app.services import fx
from app.services.instruments import last_two


def in_watchlist(session: Session, user_id: str | None, symbol: str) -> bool:
    if user_id is None:
        return False
    return (
        session.scalar(
            select(WatchlistItem.symbol).where(
                WatchlistItem.user_id == user_id, WatchlistItem.symbol == symbol
            )
        )
        is not None
    )


def build_quote(session: Session, instrument: Instrument, followed: bool) -> Quote:
    """Latest close in EUR and its change vs the previous session (also in EUR).

    `followed`: whether the instrument is in the current user's watchlist (False when anonymous).
    """
    rows = last_two(session, instrument.symbol)
    quote = Quote(
        symbol=instrument.symbol,
        name=instrument.name,
        exchange=instrument.exchange,
        currency=instrument.currency,
        date=None,
        close=None,
        close_local=None,
        change_percent=None,
        volume=None,
        followed=followed,
    )
    if not rows:
        return quote

    latest = rows[0]
    previous = rows[1] if len(rows) > 1 else None
    converter = fx.Converter(session, instrument.currency, since=rows[-1].date)
    close = converter.to_eur(float(latest.close), latest.date)
    prev_close = converter.to_eur(float(previous.close), previous.date) if previous else None

    quote.date = latest.date
    quote.close = close
    quote.close_local = float(latest.close)
    quote.volume = latest.volume
    if close is not None and prev_close:
        quote.change_percent = (close / prev_close - 1) * 100
    return quote
