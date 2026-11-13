from typing import Annotated

from fastapi import APIRouter, Query

from app.schemas import NewsFeed
from app.services.news import get_news

router = APIRouter(tags=["news"])


@router.get("/news")
async def news(limit: Annotated[int, Query(ge=1, le=15)] = 5) -> list[NewsFeed]:
    """5 fixed financial news sources, most recent articles first. Public, no login needed."""
    return await get_news(limit)
