"""Comparison metrics computed on EUR closes."""

import bisect
import datetime as dt
import math
import statistics

TRADING_DAYS = 252


def _perf(dates: list[dt.date], closes: list[float], days: int) -> float | None:
    target = dates[-1] - dt.timedelta(days=days)
    i = bisect.bisect_right(dates, target) - 1
    if i < 0:
        # History doesn't go back far enough (allow a few days of slack for holidays).
        if dates[0] - target > dt.timedelta(days=7):
            return None
        i = 0
    base = closes[i]
    return (closes[-1] / base - 1) * 100 if base else None


def compute(points: list[tuple[dt.date, float]]) -> dict[str, float | None]:
    """points: (date, close in EUR), ascending."""
    if len(points) < 2:
        return dict.fromkeys(
            ("perf_1m", "perf_1y", "perf_5y", "volatility_1y", "high_52w", "low_52w"), None
        )
    dates = [d for d, _ in points]
    closes = [c for _, c in points]

    start_1y = dates[-1] - dt.timedelta(days=365)
    window = [c for d, c in points if d >= start_1y]
    returns = [math.log(b / a) for a, b in zip(window, window[1:]) if a > 0 and b > 0]
    volatility = (
        statistics.stdev(returns) * math.sqrt(TRADING_DAYS) * 100 if len(returns) > 20 else None
    )

    return {
        "perf_1m": _perf(dates, closes, 30),
        "perf_1y": _perf(dates, closes, 365),
        "perf_5y": _perf(dates, closes, 365 * 5),
        "volatility_1y": volatility,
        "high_52w": max(window),
        "low_52w": min(window),
    }
