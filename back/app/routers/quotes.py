from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_session
from app.models import DailyPrice
from app.schemas import HistoryPoint, Quote

router = APIRouter(prefix="/quotes", tags=["quotes"])

SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("")
def list_quotes(session: SessionDep, settings: SettingsDep) -> list[Quote]:
    quotes: list[Quote] = []
    for symbol in settings.symbols:
        last_two = session.scalars(
            select(DailyPrice)
            .where(DailyPrice.symbol == symbol)
            .order_by(DailyPrice.date.desc())
            .limit(2)
        ).all()
        if not last_two:
            continue
        latest = last_two[0]
        previous = last_two[1] if len(last_two) > 1 else None
        change = float(latest.close - previous.close) if previous else None
        change_percent = (
            float((latest.close - previous.close) / previous.close * 100) if previous else None
        )
        quotes.append(
            Quote(
                symbol=symbol,
                date=latest.date,
                open=float(latest.open),
                high=float(latest.high),
                low=float(latest.low),
                close=float(latest.close),
                volume=latest.volume,
                change=change,
                change_percent=change_percent,
            )
        )
    return quotes


@router.get("/{symbol}/history")
def symbol_history(symbol: str, session: SessionDep, settings: SettingsDep) -> list[HistoryPoint]:
    symbol = symbol.upper()
    if symbol not in settings.symbols:
        raise HTTPException(status_code=404, detail=f"Unknown symbol {symbol}")
    rows = session.scalars(
        select(DailyPrice).where(DailyPrice.symbol == symbol).order_by(DailyPrice.date)
    ).all()
    return [
        HistoryPoint(
            date=r.date,
            open=float(r.open),
            high=float(r.high),
            low=float(r.low),
            close=float(r.close),
            volume=r.volume,
        )
        for r in rows
    ]
