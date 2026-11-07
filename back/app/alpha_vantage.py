import datetime as dt
from decimal import Decimal
from typing import TypedDict

import httpx

BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantageError(Exception):
    """Alpha Vantage answered without data (rate limit, bad symbol, bad key...)."""


class DailyBar(TypedDict):
    symbol: str
    date: dt.date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


def fetch_daily(client: httpx.Client, symbol: str, api_key: str) -> list[DailyBar]:
    """Last ~100 trading days for `symbol` (TIME_SERIES_DAILY, compact)."""
    response = client.get(
        BASE_URL,
        params={
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "compact",
            "apikey": api_key,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    series = data.get("Time Series (Daily)")
    if series is None:
        # Errors come back as HTTP 200 with one of these keys.
        message = data.get("Information") or data.get("Note") or data.get("Error Message")
        raise AlphaVantageError(message or "unexpected response")

    return [
        DailyBar(
            symbol=symbol,
            date=dt.date.fromisoformat(day),
            open=Decimal(bar["1. open"]),
            high=Decimal(bar["2. high"]),
            low=Decimal(bar["3. low"]),
            close=Decimal(bar["4. close"]),
            volume=int(bar["5. volume"]),
        )
        for day, bar in series.items()
    ]
