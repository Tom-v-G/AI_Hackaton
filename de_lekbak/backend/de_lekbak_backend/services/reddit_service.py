from collections.abc import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from de_lekbak_backend.repositories.reddit_cve_repository import RedditCveRepository
from de_lekbak_backend.schemas.reddit import RedditCveEntry, RedditTrendingResponse
from de_lekbak_backend.scrapers.reddit import RedditScraper

DEFAULT_TRENDING_SUBREDDITS = ("netsec", "cybersecurity", "cve", "sysadmin")


class RedditService:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = RedditCveRepository(session)

    async def refresh_trending(
        self, subreddits: Iterable[str] = DEFAULT_TRENDING_SUBREDDITS
    ) -> RedditTrendingResponse:
        scraper = RedditScraper(repository=self._repository)
        await scraper.scrape_and_persist(subreddits)
        items = await self._repository.list_trending()
        return RedditTrendingResponse(
            items=[RedditCveEntry.model_validate(item) for item in items]
        )


def get_reddit_service(session: AsyncSession) -> RedditService:
    return RedditService(session)
