"""EUR conversion: rates stored per day, converted on read (prices stay in local currency)."""

import bisect
import datetime as dt
from functools import lru_cache

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import FxRate
from app.providers import frankfurter, yahoo
from app.providers.common import ProviderError
from app.services.upsert import upsert

FX_HISTORY_DAYS = 365 * 5 + 30


@lru_cache(maxsize=1)
def _ecb_currencies() -> frozenset[str]:
    return frozenset(frankfurter.ecb_currencies())


def ecb_currencies() -> frozenset[str]:
    try:
        return _ecb_currencies()
    except ProviderError:
        # Don't cache the failure; fall back to Yahoo for everything this time.
        return frozenset()


def _fetch(currency: str, start: dt.date) -> list[dict]:
    end = dt.date.today()
    if currency in ecb_currencies():
        data = frankfurter.rates(start, end, {currency})
        return [{"currency": c, "date": d, "rate": r} for c, d, r in data]
    return [{"currency": currency, "date": d, "rate": r} for d, r in yahoo.fx_history(currency, start)]


def ensure_currency(session: Session, currency: str | None) -> None:
    """Load the full rate history of a currency the first time it is needed."""
    if not currency or currency == "EUR":
        return
    exists = session.scalar(select(FxRate.date).where(FxRate.currency == currency).limit(1))
    if exists is None:
        start = dt.date.today() - dt.timedelta(days=FX_HISTORY_DAYS)
        upsert(session, FxRate, _fetch(currency, start), ("currency", "date"), ("rate",))
        session.commit()


def refresh_all(session: Session) -> str:
    """Append the latest rates of every currency already in use."""
    currencies = set(session.scalars(select(FxRate.currency).distinct()).all())
    if not currencies:
        return "ok: no currency in use yet"
    last = dict(
        session.execute(select(FxRate.currency, func.max(FxRate.date)).group_by(FxRate.currency)).all()
    )
    end = dt.date.today()
    rows: list[dict] = []
    errors: list[str] = []

    ecb = currencies & ecb_currencies()
    if ecb:
        start = min(last[c] for c in ecb)
        rows += [
            {"currency": c, "date": d, "rate": r} for c, d, r in frankfurter.rates(start, end, ecb)
        ]
    for currency in sorted(currencies - ecb):
        try:
            rows += [
                {"currency": currency, "date": d, "rate": r}
                for d, r in yahoo.fx_history(currency, last[currency])
            ]
        except ProviderError as exc:
            errors.append(f"{currency}: {exc}")

    upsert(session, FxRate, rows, ("currency", "date"), ("rate",))
    session.commit()
    summary = f"{len(currencies)} currencies, {len(rows)} rates"
    return f"error: {summary}; {'; '.join(errors)}" if errors else f"ok: {summary}"


class Converter:
    """Converts amounts of one currency to EUR, using the last known rate on or before each date."""

    def __init__(self, session: Session, currency: str | None, since: dt.date | None = None) -> None:
        self.identity = currency == "EUR"
        self.dates: list[dt.date] = []
        self.rates: list[float] = []
        if self.identity or not currency:
            return
        stmt = select(FxRate.date, FxRate.rate).where(FxRate.currency == currency)
        if since:
            # Keep one older rate so the first requested day still has a value.
            stmt = stmt.where(FxRate.date >= since - dt.timedelta(days=10))
        for d, r in session.execute(stmt.order_by(FxRate.date)):
            self.dates.append(d)
            self.rates.append(float(r))

    def to_eur(self, amount: float, day: dt.date) -> float | None:
        if self.identity:
            return amount
        if not self.dates:
            return None
        i = bisect.bisect_right(self.dates, day) - 1
        rate = self.rates[max(i, 0)]  # before the first known rate: use the oldest one
        return amount / rate
