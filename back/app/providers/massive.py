"""Massive (ex-Polygon) client: US market only, free tier limited to 5 calls/minute."""

import datetime as dt
import threading
import time
from collections import deque
from collections.abc import Iterator
from typing import Any

import httpx

from app.providers.common import Bar, NotFoundError, ProviderError, redact, to_decimal

BASE_URL = "https://api.massive.com"
CALLS_PER_MINUTE = 5

# Ticker types kept in the catalog: common stocks, ETFs, ADRs.
CATALOG_TYPES = {"CS", "ETF", "ADRC"}


def to_yahoo(ticker: str) -> str:
    """Massive writes share classes with a dot (BRK.B), Yahoo with a dash (BRK-B)."""
    return ticker.replace(".", "-")


def to_massive(symbol: str) -> str:
    return symbol.replace("-", ".")


class _RateLimiter:
    """Process-wide sliding window: at most `calls` requests per `period` seconds."""

    def __init__(self, calls: int, period: float) -> None:
        self.calls, self.period = calls, period
        self.stamps: deque[float] = deque()
        self.lock = threading.Lock()

    def wait(self) -> None:
        with self.lock:
            while True:
                now = time.monotonic()
                while self.stamps and now - self.stamps[0] >= self.period:
                    self.stamps.popleft()
                if len(self.stamps) < self.calls:
                    self.stamps.append(now)
                    return
                time.sleep(self.period - (now - self.stamps[0]) + 0.5)


_limiter = _RateLimiter(CALLS_PER_MINUTE, 60)


class MassiveClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.http = httpx.Client(
            base_url=BASE_URL,
            # Key in a header: it never appears in URLs, pagination links or logs.
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60,
        )

    def close(self) -> None:
        self.http.close()

    def __enter__(self) -> "MassiveClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        _limiter.wait()
        try:
            response = self.http.get(url, params=params)
        except httpx.HTTPError as exc:
            raise ProviderError(f"Massive unreachable ({type(exc).__name__})") from None
        try:
            data = response.json()
        except ValueError:
            data = {}
        if response.status_code == 404:
            raise NotFoundError("Massive: not found")
        if response.status_code != 200:
            detail = data.get("message") or data.get("error") or ""
            raise ProviderError(redact(f"Massive HTTP {response.status_code} {detail}", self.api_key))
        return data

    def grouped_daily(self, day: dt.date) -> list[Bar]:
        """Every US ticker's bar for `day` in one call. Empty list if the market was closed."""
        data = self._get(
            f"/v2/aggs/grouped/locale/us/market/stocks/{day.isoformat()}",
            {"adjusted": "false"},
        )
        return [
            Bar(
                symbol=to_yahoo(r["T"]),
                date=day,
                open=to_decimal(r["o"]),
                high=to_decimal(r["h"]),
                low=to_decimal(r["l"]),
                close=to_decimal(r["c"]),
                volume=round(r.get("v") or 0),
            )
            for r in data.get("results") or []
            if all(k in r for k in ("T", "o", "h", "l", "c"))
        ]

    def daily_range(self, symbol: str, start: dt.date, end: dt.date) -> list[Bar]:
        """Daily bars for one ticker. The free tier only serves the last 2 years."""
        data = self._get(
            f"/v2/aggs/ticker/{to_massive(symbol)}/range/1/day/{start.isoformat()}/{end.isoformat()}",
            {"adjusted": "false", "sort": "asc", "limit": 50000},
        )
        results = data.get("results") or []
        if not results:
            raise NotFoundError(f"Massive: no data for {symbol}")
        return [
            Bar(
                symbol=symbol,
                date=dt.datetime.fromtimestamp(r["t"] / 1000, dt.UTC).date(),
                open=to_decimal(r["o"]),
                high=to_decimal(r["h"]),
                low=to_decimal(r["l"]),
                close=to_decimal(r["c"]),
                volume=round(r.get("v") or 0),
            )
            for r in results
        ]

    def splits(self, start: dt.date, end: dt.date) -> set[str]:
        """Tickers (Yahoo format) with a split executed between `start` and `end` inclusive."""
        data = self._get(
            "/v3/reference/splits",
            {
                "execution_date.gte": start.isoformat(),
                "execution_date.lte": end.isoformat(),
                "limit": 1000,
            },
        )
        return {to_yahoo(s["ticker"]) for s in data.get("results") or [] if s.get("ticker")}

    def iter_catalog(self) -> Iterator[list[dict[str, Any]]]:
        """Active US stocks/ETFs/ADRs, one page (up to 1000 tickers) at a time."""
        url: str | None = "/v3/reference/tickers"
        params: dict[str, Any] | None = {"market": "stocks", "active": "true", "limit": 1000}
        while url:
            data = self._get(url, params)
            yield [t for t in data.get("results") or [] if t.get("type") in CATALOG_TYPES]
            url, params = data.get("next_url"), None
