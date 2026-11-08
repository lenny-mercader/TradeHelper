from sqlalchemy.orm import Session

from app.models import Instrument
from app.schemas import Quote
from app.services import fx
from app.services.instruments import last_two


def build_quote(session: Session, instrument: Instrument) -> Quote:
    """Latest close in EUR and its change vs the previous session (also in EUR)."""
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
        followed=instrument.followed,
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
