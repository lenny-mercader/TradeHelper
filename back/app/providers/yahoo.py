"""Yahoo Finance via yfinance: worldwide coverage, unofficial (may break or be rate limited)."""

import datetime as dt
import math
from dataclasses import dataclass
from typing import Any

import yfinance as yf
from yfinance import exceptions as yf_exc

from app.providers.common import Bar, NotFoundError, ProviderError, to_decimal

# Quote sub-units: (major currency, divisor). London quotes in pence, Johannesburg in cents...
SUBUNITS = {"GBp": ("GBP", 100), "GBX": ("GBP", 100), "ZAc": ("ZAR", 100), "ILA": ("ILS", 100)}

SEARCH_TYPES = {"EQUITY", "ETF"}


def normalize_currency(currency: str | None) -> tuple[str | None, int]:
    if currency in SUBUNITS:
        return SUBUNITS[currency]
    return (currency.upper() if currency else None), 1


@dataclass
class History:
    bars: list[Bar]
    currency: str | None
    name: str | None
    exchange: str | None
    type: str | None
    # A split happened after the first returned day: older stored bars are on another scale.
    split_after_start: bool = False


def _call(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except yf_exc.YFRateLimitError:
        raise ProviderError("Yahoo rate limit") from None
    except (yf_exc.YFPricesMissingError, yf_exc.YFTzMissingError, yf_exc.YFTickerMissingError):
        raise NotFoundError("Yahoo: unknown symbol") from None
    except Exception as exc:  # network errors, Yahoo format changes...
        raise ProviderError(f"Yahoo error ({type(exc).__name__})") from None


def fetch_history(symbol: str, start: dt.date) -> History:
    """Daily bars from `start` (split-adjusted, not dividend-adjusted), in the major currency unit."""
    ticker = yf.Ticker(symbol)
    df = _call(
        ticker.history,
        start=start.isoformat(),
        interval="1d",
        auto_adjust=False,
        actions=True,
        raise_errors=True,
    )
    splits = df["Stock Splits"] if "Stock Splits" in df else None
    split_after_start = bool(splits is not None and (splits.iloc[1:].fillna(0) != 0).any())
    meta = ticker.history_metadata or {}
    currency, divisor = normalize_currency(meta.get("currency"))

    bars: list[Bar] = []
    for ts, row in df.iterrows():
        values = [row.get(c) for c in ("Open", "High", "Low", "Close")]
        if any(v is None or math.isnan(v) for v in values):
            continue
        o, h, low, c = (to_decimal(v) / divisor for v in values)
        volume = row.get("Volume")
        bars.append(
            Bar(
                symbol=symbol,
                date=ts.date(),
                open=o,
                high=h,
                low=low,
                close=c,
                volume=0 if volume is None or math.isnan(volume) else int(volume),
            )
        )
    if not bars:
        raise NotFoundError(f"Yahoo: no data for {symbol}")

    return History(
        bars=bars,
        currency=currency,
        name=meta.get("longName") or meta.get("shortName"),
        exchange=meta.get("fullExchangeName") or meta.get("exchangeName"),
        type=meta.get("instrumentType"),
        split_after_start=split_after_start,
    )


def search(query: str, limit: int = 10) -> list[dict[str, str | None]]:
    quotes = _call(lambda: yf.Search(query, max_results=limit, news_count=0).quotes)
    return [
        {
            "symbol": q["symbol"],
            "name": q.get("longname") or q.get("shortname"),
            "exchange": q.get("exchDisp") or q.get("exchange"),
            "type": q.get("quoteType"),
        }
        for q in quotes
        if q.get("symbol") and q.get("quoteType") in SEARCH_TYPES
    ]


def fx_history(currency: str, start: dt.date) -> list[tuple[dt.date, float]]:
    """Units of `currency` per 1 EUR, for currencies the ECB does not publish."""
    df = _call(
        yf.Ticker(f"EUR{currency}=X").history,
        start=start.isoformat(),
        interval="1d",
        raise_errors=True,
    )
    return [
        (ts.date(), float(row["Close"]))
        for ts, row in df.iterrows()
        if not math.isnan(row["Close"]) and row["Close"] > 0
    ]
