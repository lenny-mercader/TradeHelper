"""Cumulative change of several instruments over a period (public: watchlist chart, comparator)."""

from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status

from app.routers.deps import SessionDep, SettingsDep
from app.schemas import PerformanceOut, PerformanceSeries
from app.services import performance

router = APIRouter(tags=["performance"])

MAX_SYMBOLS = 10


@router.get("/performance")
def get_performance(
    session: SessionDep,
    settings: SettingsDep,
    symbols: Annotated[str, Query(description="Comma-separated, e.g. AAPL,MC.PA")],
    period: Annotated[Literal["1M", "6M", "1Y", "5Y"], Query()] = "1Y",
) -> PerformanceOut:
    """Change in % (EUR) since the period start, one value per date of the shared axis."""
    wanted = list(dict.fromkeys(s.strip().upper() for s in symbols.split(",") if s.strip()))
    if not wanted or len(wanted) > MAX_SYMBOLS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Give 1 to {MAX_SYMBOLS} symbols")

    result = performance.compute(session, settings, wanted, period)
    return PerformanceOut(
        period=period,
        start=result.start,
        end=result.end,
        dates=result.dates,
        series=[
            PerformanceSeries(
                symbol=s.symbol, name=s.name, currency=s.currency, values=s.values
            )
            for s in result.series
        ],
        errors=result.errors,
    )
