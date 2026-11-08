from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_session
from app.models import Instrument
from app.providers.common import NotFoundError, ProviderError
from app.services.instruments import InvalidSymbolError, ensure_loaded

SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@contextmanager
def provider_errors() -> Iterator[None]:
    """Map data-provider failures to HTTP errors."""
    try:
        yield
    except InvalidSymbolError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid symbol: {exc}") from None
    except NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown symbol") from None
    except ProviderError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, f"Data source unavailable: {exc}"
        ) from None


def load_instrument(session: Session, settings: Settings, symbol: str) -> Instrument:
    with provider_errors():
        return ensure_loaded(session, settings, symbol)
