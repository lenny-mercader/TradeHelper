from fastapi import APIRouter

from app.routers.deps import SessionDep, SettingsDep, load_instrument
from app.schemas import HistoryPoint, Quote
from app.services import fx, instruments
from app.services.quotes import build_quote

router = APIRouter(prefix="/instruments", tags=["instruments"])


@router.get("/{symbol}")
def get_instrument(symbol: str, session: SessionDep, settings: SettingsDep) -> Quote:
    """Loads the instrument's history on first access (Yahoo, Massive as fallback)."""
    instrument = load_instrument(session, settings, symbol)
    return build_quote(session, instrument)


@router.get("/{symbol}/history")
def get_history(symbol: str, session: SessionDep, settings: SettingsDep) -> list[HistoryPoint]:
    instrument = load_instrument(session, settings, symbol)
    rows = instruments.history(session, instrument.symbol)
    converter = fx.Converter(session, instrument.currency, since=rows[0].date if rows else None)
    return [
        HistoryPoint(
            date=r.date,
            close=converter.to_eur(float(r.close), r.date),
            close_local=float(r.close),
            volume=r.volume,
        )
        for r in rows
    ]
