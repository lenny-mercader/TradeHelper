from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.providers.common import NotFoundError, ProviderError
from app.routers.deps import SessionDep, SettingsDep
from app.schemas import CompareRow
from app.services import fx, instruments, metrics
from app.services.instruments import InvalidSymbolError
from app.services.quotes import build_quote

router = APIRouter(tags=["compare"])

MAX_SYMBOLS = 10


@router.get("/compare")
def compare(
    session: SessionDep,
    settings: SettingsDep,
    symbols: Annotated[str, Query(description="Comma-separated, e.g. AAPL,MC.PA")],
) -> list[CompareRow]:
    wanted = list(dict.fromkeys(s.strip().upper() for s in symbols.split(",") if s.strip()))
    if not wanted or len(wanted) > MAX_SYMBOLS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Give 1 to {MAX_SYMBOLS} symbols")

    rows: list[CompareRow] = []
    for symbol in wanted:
        try:
            instrument = instruments.ensure_loaded(session, settings, symbol)
        except InvalidSymbolError:
            rows.append(CompareRow(symbol=symbol, error="Symbole invalide"))
            continue
        except NotFoundError:
            rows.append(CompareRow(symbol=symbol, error="Symbole inconnu"))
            continue
        except ProviderError:
            rows.append(CompareRow(symbol=symbol, error="Source de données indisponible"))
            continue

        history = instruments.history(session, instrument.symbol)
        converter = fx.Converter(session, instrument.currency)
        points = [
            (r.date, eur)
            for r in history
            if (eur := converter.to_eur(float(r.close), r.date)) is not None
        ]
        rows.append(
            CompareRow(
                symbol=instrument.symbol,
                name=instrument.name,
                currency=instrument.currency,
                close=build_quote(session, instrument, followed=False).close,
                **metrics.compute(points),
            )
        )
    return rows
