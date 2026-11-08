import datetime as dt
from decimal import Decimal
from typing import TypedDict


class ProviderError(Exception):
    """A data provider could not answer (rate limit, network, outage...)."""


class NotFoundError(ProviderError):
    """The provider does not know this symbol."""


class Bar(TypedDict):
    symbol: str
    date: dt.date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


def to_decimal(value: float | int | str) -> Decimal:
    return Decimal(str(value))


def redact(message: str, *secrets: str) -> str:
    """Remove secrets (API keys...) from a message before it reaches logs or API responses."""
    for secret in secrets:
        if secret:
            message = message.replace(secret, "***")
    return message
