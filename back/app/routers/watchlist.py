"""The signed-in user's watchlist. Every route requires a Clerk session."""

import datetime as dt

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert

from app.auth import CurrentUser
from app.models import Instrument, WatchlistItem
from app.routers.deps import SessionDep, SettingsDep, load_instrument
from app.schemas import Quote
from app.services.instruments import normalize_symbol
from app.services.quotes import build_quote

router = APIRouter(prefix="/watchlist", tags=["watchlist"])

MAX_FAVORITES = 5


@router.get("")
def list_watchlist(session: SessionDep, user_id: CurrentUser) -> list[Quote]:
    rows = session.execute(
        select(Instrument, WatchlistItem.favorite)
        .join(WatchlistItem, WatchlistItem.symbol == Instrument.symbol)
        .where(WatchlistItem.user_id == user_id)
        .order_by(Instrument.symbol)
    ).all()
    return [build_quote(session, i, followed=True, favorite=fav) for i, fav in rows]


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


@router.post("/{symbol}/favorite")
def favorite(symbol: str, session: SessionDep, user_id: CurrentUser) -> Quote:
    """Star a followed stock (max 5 per user: unstar one to free a slot)."""
    symbol = normalize_symbol(symbol)
    row = session.get(WatchlistItem, (user_id, symbol))
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cette action n'est pas suivie")
    if not row.favorite:
        count = session.scalar(
            select(func.count())
            .select_from(WatchlistItem)
            .where(WatchlistItem.user_id == user_id, WatchlistItem.favorite)
        )
        if count >= MAX_FAVORITES:
            raise HTTPException(
                status.HTTP_409_CONFLICT, f"Maximum {MAX_FAVORITES} favoris : retires-en un d'abord"
            )
        row.favorite = True
        row.favorited_at = dt.datetime.now(dt.UTC)
        session.commit()
    instrument = session.get(Instrument, symbol)
    assert instrument is not None  # the foreign key guarantees it
    return build_quote(session, instrument, followed=True, favorite=True)


@router.delete("/{symbol}/favorite")
def unfavorite(symbol: str, session: SessionDep, user_id: CurrentUser) -> Quote:
    symbol = normalize_symbol(symbol)
    session.execute(
        update(WatchlistItem)
        .where(WatchlistItem.user_id == user_id, WatchlistItem.symbol == symbol)
        .values(favorite=False, favorited_at=None)
    )
    session.commit()
    instrument = session.get(Instrument, symbol)
    if instrument is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cette action n'est pas suivie")
    return build_quote(session, instrument, followed=True, favorite=False)
