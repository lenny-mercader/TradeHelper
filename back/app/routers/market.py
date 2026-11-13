from typing import Annotated

from fastapi import APIRouter, Query

from app.routers.deps import SessionDep
from app.schemas import Heatmap, Movers
from app.services import market

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/movers")
def get_movers(session: SessionDep) -> Movers:
    """Biggest US gainers/losers of the last session (liquid stocks above 1 USD)."""
    data = market.movers(session)
    return Movers(date=market.snapshot_date(session), **data)


@router.get("/heatmap")
def get_heatmap(session: SessionDep, limit: Annotated[int, Query(ge=1, le=200)] = 100) -> Heatmap:
    """Top US stocks by dollar volume, for the homepage heatmap."""
    return Heatmap(date=market.snapshot_date(session), tiles=market.heatmap(session, limit))
