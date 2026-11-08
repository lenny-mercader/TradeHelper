"""Scheduled jobs, called by GitHub Actions with a shared bearer token."""

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.routers.deps import SessionDep, SettingsDep
from app.schemas import JobResult
from app.services.refresh import catalog_refresh, daily_refresh

bearer = HTTPBearer()


def require_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)], settings: SettingsDep
) -> None:
    if not secrets.compare_digest(credentials.credentials, settings.refresh_token):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")


router = APIRouter(tags=["jobs"], dependencies=[Depends(require_token)])


def _respond(results: dict[str, str]) -> JobResult | JSONResponse:
    result = JobResult(results=results)
    if any(v.startswith("error") for v in results.values()):
        # Non-2xx so the scheduled workflow shows up as failed.
        return JSONResponse(status_code=502, content=result.model_dump())
    return result


@router.post("/refresh", responses={502: {"model": JobResult}})
def refresh(session: SessionDep, settings: SettingsDep) -> JobResult:
    """Nightly: US snapshot (1 Massive call), followed instruments, FX rates."""
    return _respond(daily_refresh(session, settings))


@router.post("/catalog/refresh", responses={502: {"model": JobResult}})
def refresh_catalog(session: SessionDep, settings: SettingsDep) -> JobResult:
    """Weekly: US instrument catalog (~13 Massive calls, about 3 minutes)."""
    return _respond(catalog_refresh(session, settings))
