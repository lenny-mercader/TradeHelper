import datetime as dt
from decimal import Decimal
from typing import TypedDict

import httpx

BASE_URL = "https://api.tiingo.com/tiingo/daily"


class TiingoError(Exception):
    """Tiingo refused the request (unknown ticker, quota exceeded, bad key...)."""


class DailyBar(TypedDict):
    symbol: str
    date: dt.date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


def fetch_daily(
    client: httpx.Client, symbol: str, api_key: str, start_date: dt.date
) -> list[DailyBar]:
    """Raw (unadjusted) end-of-day bars for `symbol` from `start_date` to today."""
    response = client.get(
        f"{BASE_URL}/{symbol}/prices",
        params={"startDate": start_date.isoformat()},
        # Key in a header rather than the query string, so it never shows up in URLs or logs.
        headers={"Authorization": f"Token {api_key}"},
        timeout=60,
    )
    try:
        data = response.json()
    except ValueError:
        data = None

    if response.status_code != 200 or not isinstance(data, list):
        detail = data.get("detail") if isinstance(data, dict) else None
        raise TiingoError(detail or f"HTTP {response.status_code}")

    return [
        DailyBar(
            symbol=symbol,
            date=dt.date.fromisoformat(bar["date"][:10]),
            open=Decimal(str(bar["open"])),
            high=Decimal(str(bar["high"])),
            low=Decimal(str(bar["low"])),
            close=Decimal(str(bar["close"])),
            volume=int(bar["volume"]),
        )
        for bar in data
    ]
