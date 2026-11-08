"""US catalog (~12k stocks/ETFs/ADRs) from Massive, for instant local search."""

from sqlalchemy.orm import Session

from app.models import Instrument
from app.providers.massive import MassiveClient, to_yahoo
from app.services.upsert import upsert


def refresh_catalog(session: Session, massive: MassiveClient) -> str:
    total = 0
    for page in massive.iter_catalog():
        rows = [
            {
                "symbol": to_yahoo(t["ticker"]),
                "name": t.get("name"),
                "exchange": t.get("primary_exchange"),
                "currency": (t.get("currency_name") or "usd").upper(),
                "type": t.get("type"),
                "is_us": True,
            }
            for t in page
        ]
        # Never touch history columns: only descriptive fields are refreshed.
        upsert(session, Instrument, rows, ("symbol",), ("name", "exchange", "currency", "type", "is_us"))
        session.commit()
        total += len(rows)
    return f"ok: {total} US instruments"
