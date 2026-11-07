import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_session
from app.refresh import refresh_all
from app.schemas import RefreshResult

router = APIRouter(tags=["refresh"])

bearer = HTTPBearer()


def require_refresh_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    if not secrets.compare_digest(credentials.credentials, settings.refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@router.post(
    "/refresh",
    dependencies=[Depends(require_refresh_token)],
    responses={502: {"model": RefreshResult}},
)
def refresh(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RefreshResult:
    """Pull end-of-day data from Alpha Vantage. Called daily by GitHub Actions."""
    result = RefreshResult(results=refresh_all(session, settings))
    if any(r.startswith("error") for r in result.results.values()):
        # Non-2xx so the scheduled workflow shows up as failed.
        return JSONResponse(status_code=502, content=result.model_dump())
    return result
