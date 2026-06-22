from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from de_lekbak_backend.db.session import get_async_session
from de_lekbak_backend.schemas.reddit import RedditTrendingResponse
from de_lekbak_backend.services.reddit_service import DEFAULT_TRENDING_SUBREDDITS, RedditService
from de_lekbak_backend.services.reddit_service import get_reddit_service as build_reddit_service

router = APIRouter()


async def get_reddit_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> RedditService:
    return build_reddit_service(session)


@router.post("/trending", response_model=RedditTrendingResponse)
@router.get("/trending", response_model=RedditTrendingResponse)
async def refresh_reddit_trending(
    service: Annotated[RedditService, Depends(get_reddit_service)],
    subreddits: Annotated[
        list[str] | None,
        Query(description="Subreddits to scrape for CVE mentions."),
    ] = None,
) -> RedditTrendingResponse:
    return await service.refresh_trending(subreddits or DEFAULT_TRENDING_SUBREDDITS)
