"""ECB reference rates via the free Frankfurter API (no key, ~30 currencies, since 1999)."""

import datetime as dt

import httpx

from app.providers.common import ProviderError

BASE_URL = "https://api.frankfurter.dev/v1"

# Fetch long ranges one year at a time to keep responses small and complete.
CHUNK = dt.timedelta(days=365)


def ecb_currencies() -> set[str]:
    try:
        response = httpx.get(f"{BASE_URL}/currencies", timeout=30)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ProviderError(f"Frankfurter unreachable ({type(exc).__name__})") from None
    return set(response.json())


def rates(
    start: dt.date, end: dt.date, currencies: set[str] | None = None
) -> list[tuple[str, dt.date, float]]:
    """(currency, date, units per 1 EUR) for every ECB publication day in [start, end]."""
    out: list[tuple[str, dt.date, float]] = []
    with httpx.Client(timeout=60) as client:
        chunk_start = start
        while chunk_start <= end:
            chunk_end = min(chunk_start + CHUNK, end)
            params = {"base": "EUR"}
            if currencies:
                params["symbols"] = ",".join(sorted(currencies))
            try:
                response = client.get(
                    f"{BASE_URL}/{chunk_start.isoformat()}..{chunk_end.isoformat()}", params=params
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise ProviderError(f"Frankfurter error ({type(exc).__name__})") from None
            for day, by_currency in response.json().get("rates", {}).items():
                for currency, value in by_currency.items():
                    out.append((currency, dt.date.fromisoformat(day), float(value)))
            chunk_start = chunk_end + dt.timedelta(days=1)
    return out
