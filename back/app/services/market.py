"""Whole US market from one Massive grouped call per day."""

import datetime as dt

from sqlalchemy import case, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import DailyPrice, Instrument, UsSnapshot
from app.providers.common import Bar
from app.providers.massive import MassiveClient
from app.services import fx
from app.services.instruments import save_bars

# How far back to look for the last trading day (weekends, holidays, data not published yet).
LOOKBACK_DAYS = 6

# Longest acceptable hole between an opened instrument's last bar and the new session
# (a long weekend); beyond that, nights were missed and the history must be reloaded.
MAX_GAP = dt.timedelta(days=5)

# Movers: ignore penny stocks and illiquid tickers.
MIN_PRICE = 1
MIN_VOLUME = 200_000


def _last_trading_day(massive: MassiveClient, before: dt.date) -> tuple[dt.date, list[Bar]] | None:
    for back in range(LOOKBACK_DAYS):
        day = before - dt.timedelta(days=back)
        if day.weekday() >= 5:
            continue
        bars = massive.grouped_daily(day)
        if bars:
            return day, bars
    return None


def _store_snapshot(session: Session, bars: list[Bar]) -> None:
    """Upsert, keeping the previous close when the date moves forward."""
    for i in range(0, len(bars), 5000):
        stmt = insert(UsSnapshot).values([{**b, "prev_close": None} for b in bars[i : i + 5000]])
        newer = UsSnapshot.date < stmt.excluded.date
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol"],
            set_={
                "prev_close": case((newer, UsSnapshot.close), else_=UsSnapshot.prev_close),
                **{c: stmt.excluded[c] for c in ("date", "open", "high", "low", "close", "volume")},
            },
        )
        session.execute(stmt)


def refresh_snapshot(
    session: Session, massive: MassiveClient
) -> tuple[str, dt.date | None, set[str]]:
    """Store the latest US session. Returns (status, day, opened symbols updated from it)."""
    found = _last_trading_day(massive, dt.date.today())
    if not found:
        return "error: no US trading day found in the last days", None, set()
    day, bars = found

    current = session.scalar(select(func.max(UsSnapshot.date)))
    if current is None:
        # First run: load the previous session too, so daily changes exist right away.
        previous = _last_trading_day(massive, day - dt.timedelta(days=1))
        if previous:
            _store_snapshot(session, previous[1])
            current = previous[0]
    if current != day:
        _store_snapshot(session, bars)

    # Splits since the previous session (at least those executed on the session day itself):
    # flagged so movers skip them, as raw close vs prev_close jumps by the split ratio.
    split_start = current + dt.timedelta(days=1) if current and current < day else day
    split_symbols = massive.splits(split_start, day)
    session.execute(update(UsSnapshot).values(split=UsSnapshot.symbol.in_(split_symbols)))

    # Append the day to opened US instruments whose history is complete and continuous.
    # The others (gap, split, never fully loaded) are reloaded from Yahoo/Massive by the caller.
    last_dates = session.execute(
        select(Instrument.symbol, Instrument.history_loaded_at, func.max(DailyPrice.date))
        .outerjoin(DailyPrice, DailyPrice.symbol == Instrument.symbol)
        .where(Instrument.history_checked_on.is_not(None), Instrument.is_us)
        .group_by(Instrument.symbol, Instrument.history_loaded_at)
    ).all()
    covered = {
        symbol
        for symbol, loaded_at, last in last_dates
        if loaded_at is not None
        and last is not None
        and day - last <= MAX_GAP
        and symbol not in split_symbols
    }
    save_bars(session, [b for b in bars if b["symbol"] in covered])
    # A split makes the stored (split-adjusted) history stale: force a full reload.
    session.execute(
        update(Instrument)
        .where(Instrument.symbol.in_(split_symbols), Instrument.history_loaded_at.is_not(None))
        .values(history_loaded_at=None)
    )
    session.commit()
    fx.ensure_currency(session, "USD")
    return f"ok: {len(bars)} tickers on {day.isoformat()}", day, covered


def _tradable_snapshot():
    """Liquid, non-split US common stocks/ADRs with a known previous close."""
    change = (UsSnapshot.close - UsSnapshot.prev_close) / UsSnapshot.prev_close
    return (
        select(UsSnapshot, Instrument.name, change.label("change"))
        .join(Instrument, Instrument.symbol == UsSnapshot.symbol)
        .where(
            UsSnapshot.prev_close.is_not(None),
            UsSnapshot.prev_close > 0,
            UsSnapshot.split.is_(False),
            UsSnapshot.close >= MIN_PRICE,
            UsSnapshot.volume >= MIN_VOLUME,
            Instrument.type.in_(("CS", "ADRC")),
        )
    )


def movers(session: Session, limit: int = 10) -> dict[str, list[dict]]:
    base = _tradable_snapshot()
    usd = fx.Converter(session, "USD")

    def rows(order) -> list[dict]:
        out = []
        for snap, name, chg in session.execute(base.order_by(order).limit(limit)):
            out.append(
                {
                    "symbol": snap.symbol,
                    "name": name,
                    "date": snap.date,
                    "close": usd.to_eur(float(snap.close), snap.date),
                    "close_local": float(snap.close),
                    "currency": "USD",
                    "change_percent": float(chg) * 100,
                    "volume": snap.volume,
                }
            )
        return out

    change = base.selected_columns.change
    return {"gainers": rows(change.desc()), "losers": rows(change.asc())}


def heatmap(session: Session, limit: int = 100) -> list[dict]:
    """Top `limit` US stocks by dollar volume (close * volume), a free proxy for company size
    (no market cap in our data sources): each tile's area is meant to reflect that share.
    """
    base = _tradable_snapshot()
    dollar_volume = (UsSnapshot.close * UsSnapshot.volume).label("dollar_volume")
    usd = fx.Converter(session, "USD")

    rows = session.execute(
        base.add_columns(dollar_volume).order_by(dollar_volume.desc()).limit(limit)
    ).all()
    return [
        {
            "symbol": snap.symbol,
            "name": name,
            "close": usd.to_eur(float(snap.close), snap.date),
            "close_local": float(snap.close),
            "currency": "USD",
            "change_percent": float(chg) * 100,
            "volume": snap.volume,
            "dollar_volume": float(dv),
        }
        for snap, name, chg, dv in rows
    ]


def snapshot_date(session: Session) -> dt.date | None:
    return session.scalar(select(func.max(UsSnapshot.date)))


def last_stored(session: Session, symbol: str) -> dt.date | None:
    return session.scalar(select(func.max(DailyPrice.date)).where(DailyPrice.symbol == symbol))
