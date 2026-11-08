from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import case, func, or_, select

from app.models import Instrument
from app.providers import yahoo
from app.providers.common import ProviderError
from app.routers.deps import SessionDep
from app.schemas import SearchResult

router = APIRouter(tags=["search"])

LOCAL_LIMIT = 8
TOTAL_LIMIT = 15


def _like_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("/search")
def search(
    session: SessionDep, q: Annotated[str, Query(min_length=1, max_length=64)]
) -> list[SearchResult]:
    """Known instruments first (US catalog + already opened), then Yahoo for the rest of the world."""
    query = q.strip()
    upper = query.upper()
    pattern = _like_escape(query)
    local = session.scalars(
        select(Instrument)
        .where(
            or_(
                Instrument.symbol.ilike(f"{_like_escape(upper)}%", escape="\\"),
                Instrument.name.ilike(f"%{pattern}%", escape="\\"),
            )
        )
        .order_by(
            # Exact ticker, ticker prefix, name prefix, a word of the name, anything else.
            case(
                (Instrument.symbol == upper, 0),
                (Instrument.symbol.ilike(f"{pattern}%", escape="\\"), 1),
                (Instrument.name.ilike(f"{pattern}%", escape="\\"), 2),
                (Instrument.name.ilike(f"% {pattern}%", escape="\\"), 3),
                else_=4,
            ),
            # Among equals, prefer stocks over ETFs, then shorter names (usually the main listing).
            case((Instrument.type == "ETF", 1), else_=0),
            func.length(Instrument.name),
        )
        .limit(LOCAL_LIMIT)
    ).all()
    results = [
        SearchResult(symbol=i.symbol, name=i.name, exchange=i.exchange, type=i.type) for i in local
    ]

    try:
        remote = yahoo.search(query)
    except ProviderError:
        remote = []  # Yahoo blocked or down: local results only
    seen = {r.symbol for r in results}
    for item in remote:
        if item["symbol"] not in seen and len(results) < TOTAL_LIMIT:
            results.append(SearchResult(**item))
            seen.add(item["symbol"])
    return results
