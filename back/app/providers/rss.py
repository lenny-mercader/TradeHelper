"""RSS/Atom fetch (feedparser handles both formats and malformed XML).

Most financial news sites reject requests with no identifying User-Agent (curl's default gets a
plain 403). This is a normal RSS reader, not a browser impersonation, so the header names the app
honestly instead of spoofing a browser.
"""

import datetime as dt

import feedparser
import httpx

USER_AGENT = "TradeHelper-RSS-Reader/1.0 (+https://trade-helper-rho.vercel.app)"
TIMEOUT_S = 10


class FeedError(Exception):
    """The feed could not be fetched or contained no readable entries."""


def _entry_image(entry: feedparser.FeedParserDict) -> str | None:
    media = entry.get("media_content") or entry.get("media_thumbnail")
    if media and media[0].get("url"):
        return media[0]["url"]
    for enc in entry.get("links", []):
        if enc.get("rel") == "enclosure" and str(enc.get("type", "")).startswith("image/"):
            return enc.get("href")
    return None


def _entry_date(entry: feedparser.FeedParserDict) -> dt.datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return dt.datetime(*parsed[:6], tzinfo=dt.UTC)


async def fetch(client: httpx.AsyncClient, url: str, limit: int) -> list[dict]:
    """Up to `limit` entries: title, url, published_at (UTC or None), image_url (or None)."""
    try:
        response = await client.get(
            url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_S, follow_redirects=True
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise FeedError(f"{type(exc).__name__}") from None

    parsed = feedparser.parse(response.content)
    if parsed.bozo and not parsed.entries:
        raise FeedError("flux illisible")
    if not parsed.entries:
        raise FeedError("flux vide")

    return [
        {
            "title": e.get("title", "").strip(),
            "url": e.get("link", ""),
            "published_at": _entry_date(e),
            "image_url": _entry_image(e),
        }
        for e in parsed.entries[:limit]
        if e.get("title") and e.get("link")
    ]
