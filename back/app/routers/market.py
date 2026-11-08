from fastapi import APIRouter

from app.routers.deps import SessionDep
from app.schemas import Movers
from app.services import market

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/movers")
def get_movers(session: SessionDep) -> Movers:
    """Biggest US gainers/losers of the last session (liquid stocks above 1 USD)."""
    data = market.movers(session)
    return Movers(date=market.snapshot_date(session), **data)
