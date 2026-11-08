"""The signed-in user's watchlist. Every route requires a Clerk session."""

from fastapi import APIRouter, status
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from app.auth import CurrentUser
from app.models import Instrument, WatchlistItem
from app.routers.deps import SessionDep, SettingsDep, load_instrument
from app.schemas import Quote
from app.services.instruments import normalize_symbol
from app.services.quotes import build_quote

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("")
def list_watchlist(session: SessionDep, user_id: CurrentUser) -> list[Quote]:
    instruments = session.scalars(
        select(Instrument)
        .join(WatchlistItem, WatchlistItem.symbol == Instrument.symbol)
        .where(WatchlistItem.user_id == user_id)
        .order_by(Instrument.symbol)
    ).all()
    return [build_quote(session, i, followed=True) for i in instruments]


@router.post("/{symbol}")
def follow(symbol: str, session: SessionDep, settings: SettingsDep, user_id: CurrentUser) -> Quote:
    instrument = load_instrument(session, settings, symbol)
    session.execute(
        insert(WatchlistItem)
        .values(user_id=user_id, symbol=instrument.symbol)
        .on_conflict_do_nothing(index_elements=["user_id", "symbol"])
    )
    session.commit()
    return build_quote(session, instrument, followed=True)


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
def unfollow(symbol: str, session: SessionDep, user_id: CurrentUser) -> None:
    session.execute(
        delete(WatchlistItem).where(
            WatchlistItem.user_id == user_id, WatchlistItem.symbol == normalize_symbol(symbol)
        )
    )
    session.commit()
