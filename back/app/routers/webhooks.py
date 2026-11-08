"""Clerk webhooks (signed with Svix). Public route: authenticity comes from the signature."""

import json
import logging

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import delete
from svix.webhooks import Webhook, WebhookVerificationError

from app.models import WatchlistItem
from app.routers.deps import SessionDep, SettingsDep

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
log = logging.getLogger(__name__)

SVIX_HEADERS = ("svix-id", "svix-timestamp", "svix-signature")


@router.post("/clerk", status_code=status.HTTP_204_NO_CONTENT)
async def clerk_webhook(request: Request, session: SessionDep, settings: SettingsDep) -> Response:
    if not settings.clerk_webhook_signing_secret:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Webhook not configured")

    body = await request.body()
    headers = {h: request.headers.get(h, "") for h in SVIX_HEADERS}
    try:
        # svix >= 2.9 only verifies (returns None); the body is parsed once it is trusted.
        Webhook(settings.clerk_webhook_signing_secret).verify(body, headers)
    except WebhookVerificationError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid signature") from None
    event = json.loads(body)

    if event.get("type") == "user.deleted":
        user_id = (event.get("data") or {}).get("id")
        if user_id:
            # Account deleted (by the user or an admin): erase their data (GDPR).
            result = session.execute(delete(WatchlistItem).where(WatchlistItem.user_id == user_id))
            session.commit()
            log.info("Deleted %s watchlist items of a deleted Clerk user", result.rowcount)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
