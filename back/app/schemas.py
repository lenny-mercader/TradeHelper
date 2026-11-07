import datetime as dt

from pydantic import BaseModel


class Quote(BaseModel):
    """Latest end-of-day bar of a symbol, compared with the previous one."""

    symbol: str
    date: dt.date
    open: float
    high: float
    low: float
    close: float
    volume: int
    change: float | None
    change_percent: float | None


class HistoryPoint(BaseModel):
    date: dt.date
    open: float
    high: float
    low: float
    close: float
    volume: int


class RefreshResult(BaseModel):
    results: dict[str, str]
