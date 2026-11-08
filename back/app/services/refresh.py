"""Scheduled jobs (run by GitHub Actions through `python -m app.jobs`).

Nightly: US snapshot, every already-opened instrument the snapshot doesn't cover, then FX rates.
"""

import datetime as dt
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Instrument
from app.providers.common import ProviderError, redact
from app.providers.massive import MassiveClient
from app.services import fx, instruments, market
from app.services.catalog import refresh_catalog


def daily_refresh(session: Session, settings: Settings) -> dict[str, str]:
    results: dict[str, str] = {}

    def guard(name: str, fn: Callable[[], None]) -> None:
        """Run one step; record its failure without stopping the others."""
        try:
            fn()
        except ProviderError as exc:
            session.rollback()
            results[name] = redact(f"error: {exc}", settings.massive_api_key)
        except Exception as exc:
            session.rollback()
            # First line only: database errors embed the whole SQL statement.
            first_line = str(exc).splitlines()[0][:300] if str(exc) else ""
            results[name] = redact(
                f"error: {type(exc).__name__}: {first_line}", settings.massive_api_key
            )

    covered: set[str] = set()

    def snapshot() -> None:
        with MassiveClient(settings.massive_api_key) as massive:
            message, _, symbols = market.refresh_snapshot(session, massive)
        results["us_snapshot"] = message
        covered.update(symbols)

    guard("us_snapshot", snapshot)

    today = dt.date.today()
    # Every instrument opened at least once, whether or not someone has it in a watchlist.
    opened = session.scalars(
        select(Instrument).where(Instrument.history_checked_on.is_not(None))
    ).all()
    for instrument in opened:
        symbol = instrument.symbol
        if symbol in covered:
            instrument.history_checked_on = today
            session.commit()
            continue
        # International, or US with missed nights: incremental load (Yahoo, then Massive).
        instrument.history_checked_on = None
        session.commit()

        def load(symbol: str = symbol) -> None:
            instruments.ensure_loaded(session, settings, symbol)
            results[symbol] = f"ok: up to {market.last_stored(session, symbol)}"

        guard(symbol, load)

    def rates() -> None:
        results["fx"] = fx.refresh_all(session)

    guard("fx", rates)
    return results


def catalog_refresh(session: Session, settings: Settings) -> dict[str, str]:
    try:
        with MassiveClient(settings.massive_api_key) as massive:
            return {"catalog": refresh_catalog(session, massive)}
    except ProviderError as exc:
        session.rollback()
        return {"catalog": redact(f"error: {exc}", settings.massive_api_key)}
