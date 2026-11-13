"""Financial news: 5 fixed RSS sources, fetched concurrently and cached briefly in-process.

No database table: the free Render instance can restart or sleep, losing the cache, which just
means the next request refetches. Each feed is cached and retried independently, so one slow or
broken source never holds up the others.
"""

import asyncio
import datetime as dt
from urllib.parse import urlparse

import httpx

from app.providers.rss import FeedError, fetch
from app.schemas import NewsArticle, NewsFeed

CACHE_TTL = dt.timedelta(minutes=15)
# Fetched and cached once per feed; both the homepage (5) and the Actualité page (15) slice this.
MAX_CACHED_ARTICLES = 15

FEEDS = [
    {
        "id": "cnbc",
        "name": "CNBC",
        "site_url": "https://www.cnbc.com",
        "feed_url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    },
    {
        "id": "marketwatch",
        "name": "MarketWatch",
        "site_url": "https://www.marketwatch.com",
        "feed_url": "https://www.marketwatch.com/rss/topstories",
    },
    {
        "id": "wsj",
        "name": "Wall Street Journal",
        "site_url": "https://www.wsj.com",
        "feed_url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    },
    {
        "id": "bloomberg",
        "name": "Bloomberg Markets",
        "site_url": "https://www.bloomberg.com",
        "feed_url": "https://feeds.bloomberg.com/markets/news.rss",
    },
    {
        "id": "investing",
        "name": "Investing.com",
        "site_url": "https://www.investing.com",
        "feed_url": "https://www.investing.com/rss/news.rss",
    },
]


def _logo_url(site_url: str) -> str:
    domain = urlparse(site_url).netloc
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=64"


# Process-wide cache: {feed_id: (fetched_at, NewsFeed)}. Lost on restart, rebuilt on next request.
_cache: dict[str, tuple[dt.datetime, NewsFeed]] = {}


async def _refresh(client: httpx.AsyncClient, source: dict) -> NewsFeed:
    try:
        entries = await fetch(client, source["feed_url"], MAX_CACHED_ARTICLES)
        articles = [NewsArticle(**e) for e in entries]
        error = None
    except FeedError as exc:
        articles = []
        error = f"Source indisponible ({exc})"
    return NewsFeed(
        id=source["id"],
        name=source["name"],
        site_url=source["site_url"],
        logo_url=_logo_url(source["site_url"]),
        articles=articles,
        error=error,
    )


async def get_news(limit: int) -> list[NewsFeed]:
    """Each feed's latest articles, refreshing per-feed caches older than CACHE_TTL."""
    now = dt.datetime.now(dt.UTC)
    stale = [s for s in FEEDS if (cached := _cache.get(s["id"])) is None or now - cached[0] > CACHE_TTL]

    if stale:
        async with httpx.AsyncClient() as client:
            refreshed = await asyncio.gather(*(_refresh(client, s) for s in stale))
        for source, feed in zip(stale, refreshed, strict=True):
            # A transient failure keeps the previous (stale but non-empty) cache when one exists.
            if feed.error and source["id"] in _cache and _cache[source["id"]][1].articles:
                continue
            _cache[source["id"]] = (now, feed)

    return [
        feed.model_copy(update={"articles": feed.articles[:limit]})
        for _, feed in (_cache[s["id"]] for s in FEEDS)
    ]
