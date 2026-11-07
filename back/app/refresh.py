import datetime as dt

import httpx
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import DailyPrice
from app.tiingo import TiingoError, fetch_daily

# A symbol whose oldest stored bar is within this margin of the target start counts as fully loaded.
HISTORY_MARGIN = dt.timedelta(days=10)


def start_date_for(session: Session, symbol: str, history_start: dt.date) -> dt.date:
    """Full load if the symbol lacks history, otherwise only from its last stored day."""
    oldest, latest = session.execute(
        select(func.min(DailyPrice.date), func.max(DailyPrice.date)).where(
            DailyPrice.symbol == symbol
        )
    ).one()
    if oldest is None or oldest > history_start + HISTORY_MARGIN:
        return history_start
    # Re-fetch the last stored day too: cheap, and fixes a bar stored before its final values.
    return latest


def refresh_all(session: Session, settings: Settings) -> dict[str, str]:
    """Fetch every tracked symbol and upsert its bars. Returns a status per symbol."""
    history_start = dt.date.today() - dt.timedelta(days=365 * settings.history_years)
    results: dict[str, str] = {}
    with httpx.Client() as client:
        for symbol in settings.symbols:
            start = start_date_for(session, symbol, history_start)
            try:
                bars = fetch_daily(client, symbol, settings.tiingo_api_key, start)
            except TiingoError as exc:
                results[symbol] = f"error: {exc}"
                continue
            except httpx.HTTPError as exc:
                results[symbol] = f"error: {type(exc).__name__}"
                continue

            if bars:
                stmt = insert(DailyPrice).values(bars)
                stmt = stmt.on_conflict_do_update(
                    index_elements=[DailyPrice.symbol, DailyPrice.date],
                    set_={
                        col: stmt.excluded[col] for col in ("open", "high", "low", "close", "volume")
                    },
                )
                session.execute(stmt)
                session.commit()
            results[symbol] = f"ok: {len(bars)} bars since {start.isoformat()}"
    return results
