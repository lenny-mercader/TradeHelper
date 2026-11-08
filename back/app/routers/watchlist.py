from fastapi import APIRouter, status
from sqlalchemy import select

from app.models import Instrument
from app.routers.deps import SessionDep, SettingsDep, load_instrument
from app.schemas import Quote
from app.services.instruments import normalize_symbol
from app.services.quotes import build_quote

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("")
def list_watchlist(session: SessionDep) -> list[Quote]:
    followed = session.scalars(
        select(Instrument).where(Instrument.followed).order_by(Instrument.symbol)
    ).all()
    return [build_quote(session, i) for i in followed]


@router.post("/{symbol}")
def follow(symbol: str, session: SessionDep, settings: SettingsDep) -> Quote:
    instrument = load_instrument(session, settings, symbol)
    instrument.followed = True
    session.commit()
    return build_quote(session, instrument)


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
def unfollow(symbol: str, session: SessionDep) -> None:
    instrument = session.get(Instrument, normalize_symbol(symbol))
    if instrument:
        instrument.followed = False
        session.commit()
