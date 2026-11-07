import time

import httpx
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.alpha_vantage import AlphaVantageError, fetch_daily
from app.config import Settings
from app.models import DailyPrice

# Stay well under Alpha Vantage's per-minute burst limit.
DELAY_BETWEEN_CALLS_S = 1.5


def refresh_all(session: Session, settings: Settings) -> dict[str, str]:
    """Fetch every tracked symbol and upsert its bars. Returns a status per symbol."""
    results: dict[str, str] = {}
    with httpx.Client() as client:
        for i, symbol in enumerate(settings.symbols):
            if i:
                time.sleep(DELAY_BETWEEN_CALLS_S)
            try:
                bars = fetch_daily(client, symbol, settings.alpha_vantage_api_key)
            except AlphaVantageError as exc:
                results[symbol] = f"error: {exc}"
                continue
            except httpx.HTTPError as exc:
                # Don't echo the exception text: it contains the request URL, API key included.
                results[symbol] = f"error: {type(exc).__name__}"
                continue

            stmt = insert(DailyPrice).values(bars)
            stmt = stmt.on_conflict_do_update(
                index_elements=[DailyPrice.symbol, DailyPrice.date],
                set_={col: stmt.excluded[col] for col in ("open", "high", "low", "close", "volume")},
            )
            session.execute(stmt)
            session.commit()
            results[symbol] = f"ok: {len(bars)} bars"
    return results
