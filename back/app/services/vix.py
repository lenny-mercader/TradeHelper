"""CBOE Volatility Index (VIX): market-wide, same value for every stock page, cached briefly."""

import datetime as dt

from app.providers import yahoo
from app.providers.common import ProviderError

CACHE_TTL = dt.timedelta(minutes=30)

# Conventional VIX bands (CBOE/industry rule of thumb), not a CNN-style score.
BANDS = (
    (12, "Volatilité très faible"),
    (20, "Volatilité faible"),
    (30, "Volatilité modérée"),
    (40, "Volatilité élevée"),
)


def label(value: float) -> str:
    for ceiling, text in BANDS:
        if value < ceiling:
            return text
    return "Volatilité extrême"


_cache: tuple[dt.datetime, float] | None = None


def get_vix() -> dict[str, float | str] | None:
    """{value, label}, or None if Yahoo is unreachable and nothing is cached yet."""
    global _cache
    now = dt.datetime.now(dt.UTC)
    if _cache is None or now - _cache[0] > CACHE_TTL:
        try:
            value = yahoo.fetch_vix()
        except ProviderError:
            value = None
        if value is not None:
            _cache = (now, value)
    if _cache is None:
        return None
    return {"value": _cache[1], "label": label(_cache[1])}
