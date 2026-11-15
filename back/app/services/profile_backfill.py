"""Backfills market cap/sector for the US catalog, a bounded batch at a time.

Loading one instrument's profile at a time (on a stock page view) never touches the other
~11,000 catalog entries nobody has opened yet. This job fills them in for the catalogue view,
paced gently and run repeatedly (see .github/workflows/profile-backfill.yml) instead of in one
burst, since Yahoo has no published quota and a burst risks degrading access for the whole app.
"""

import datetime as dt
import time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Instrument
from app.providers import yahoo
from app.providers.common import ProviderError

BATCH_SIZE = 400
DELAY_BETWEEN_CALLS_S = 0.4


def backfill(session: Session, _settings: Settings) -> dict[str, str]:
    pending = session.scalars(
        select(Instrument)
        .where(Instrument.is_us, Instrument.profile_loaded_at.is_(None))
        .order_by(Instrument.symbol)
        .limit(BATCH_SIZE)
    ).all()

    if not pending:
        return {"profiles": "ok: nothing left to backfill"}

    loaded = empty = 0
    for i, instrument in enumerate(pending):
        if i:
            time.sleep(DELAY_BETWEEN_CALLS_S)
        try:
            instrument.profile = yahoo.fetch_profile(instrument.symbol)
            loaded += 1
        except ProviderError:
            # Marked as tried either way: a permanently-empty symbol (e.g. a delisted or
            # thinly-covered ticker) must not be re-fetched by every future batch forever.
            # A real visit to its stock page still gets its own retry (see ensure_loaded).
            instrument.profile = {}
            empty += 1
        instrument.profile_loaded_at = dt.datetime.now(dt.UTC)
        session.commit()

    remaining = session.scalar(
        select(func.count(Instrument.symbol)).where(
            Instrument.is_us, Instrument.profile_loaded_at.is_(None)
        )
    )
    return {"profiles": f"ok: {loaded} loaded, {empty} empty/failed, {remaining} left"}
