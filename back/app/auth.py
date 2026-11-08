"""Clerk session verification (the `__session` cookie, sent automatically on same-origin /api calls)."""

from typing import Annotated

from clerk_backend_api.security import authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions
from fastapi import Depends, HTTPException, Request, status

from app.config import Settings, get_settings


def optional_user(
    request: Request, settings: Annotated[Settings, Depends(get_settings)]
) -> str | None:
    """Clerk user id of the caller, or None for anonymous visitors."""
    if not settings.clerk_secret_key:
        return None
    state = authenticate_request(
        request,
        AuthenticateRequestOptions(
            secret_key=settings.clerk_secret_key,
            # Only tokens issued for our own front-end origins (CSRF protection recommended by Clerk).
            authorized_parties=settings.authorized_parties,
        ),
    )
    if not state.is_signed_in or not state.payload:
        return None
    return state.payload.get("sub")


def require_user(
    user_id: Annotated[str | None, Depends(optional_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    if not settings.clerk_secret_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Authentication not configured")
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in required")
    return user_id


OptionalUser = Annotated[str | None, Depends(optional_user)]
CurrentUser = Annotated[str, Depends(require_user)]
