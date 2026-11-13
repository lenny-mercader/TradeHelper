"""Cumulative change in EUR over a period, for several instruments on a shared date axis.

Used by the watchlist chart, and meant to be reused by the comparator.
"""

import bisect
import datetime as dt
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Instrument
from app.providers.common import NotFoundError, ProviderError
from app.services import fx, instruments
from app.services.instruments import InvalidSymbolError

PERIOD_DAYS = {"1M": 30, "6M": 182, "1Y": 365, "5Y": 365 * 5}


@dataclass
class Series:
    symbol: str
    name: str | None
    currency: str | None
    values: list[float | None]


@dataclass
class Performance:
    start: dt.date | None
    end: dt.date | None
    dates: list[dt.date] = field(default_factory=list)
    series: list[Series] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)


def _eur_points(session: Session, instrument: Instrument) -> list[tuple[dt.date, float]]:
    converter = fx.Converter(session, instrument.currency)
    return [
        (r.date, eur)
        for r in instruments.history(session, instrument.symbol)
        if (eur := converter.to_eur(float(r.close), r.date)) is not None
    ]


def compute(session: Session, settings: Settings, symbols: list[str], period: str) -> Performance:
    """Each series starts at 0 % on the period start, then shows its change in EUR since then.

    Dates are the union of every series' trading days; on a day an exchange is closed,
    its previous value is carried over (continuous lines).
    """
    days = PERIOD_DAYS[period]
    loaded: list[tuple[Instrument, list[tuple[dt.date, float]]]] = []
    errors: dict[str, str] = {}

    for symbol in symbols:
        try:
            instrument = instruments.ensure_loaded(session, settings, symbol)
        except InvalidSymbolError:
            errors[symbol] = "Symbole invalide"
            continue
        except NotFoundError:
            errors[symbol] = "Symbole inconnu"
            continue
        except ProviderError:
            errors[symbol] = "Source de données indisponible"
            continue
        points = _eur_points(session, instrument)
        if len(points) < 2:
            errors[instrument.symbol] = "Historique insuffisant"
            continue
        loaded.append((instrument, points))

    if not loaded:
        return Performance(start=None, end=None, errors=errors)

    end = max(points[-1][0] for _, points in loaded)
    start = end - dt.timedelta(days=days)

    # Shared axis: every trading day of any series within the period.
    axis = sorted({d for _, points in loaded for d, _ in points if start <= d <= end})

    series: list[Series] = []
    for instrument, points in loaded:
        dates = [d for d, _ in points]
        closes = [c for _, c in points]
        # Base: last close on or before the period start (first close if history starts later).
        i0 = bisect.bisect_right(dates, start) - 1
        base_index = max(i0, 0)
        base = closes[base_index]
        first_date = dates[base_index]

        values: list[float | None] = []
        for day in axis:
            if day < first_date:
                values.append(None)  # no data yet for this instrument
                continue
            i = bisect.bisect_right(dates, day) - 1  # previous value carried over on closed days
            values.append((closes[i] / base - 1) * 100 if base else None)
        series.append(
            Series(
                symbol=instrument.symbol,
                name=instrument.name,
                currency=instrument.currency,
                values=values,
            )
        )

    return Performance(start=start, end=end, dates=axis, series=series, errors=errors)
