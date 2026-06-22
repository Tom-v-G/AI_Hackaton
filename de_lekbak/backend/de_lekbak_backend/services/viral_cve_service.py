from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from de_lekbak_backend.repositories.viral_cve_repository import ViralCveRepository
from de_lekbak_backend.schemas.viral_cve import ViralCveRankingResponse, ViralCveRefreshResponse


class ViralCveService:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = ViralCveRepository(session)

    async def list_rankings(self) -> ViralCveRankingResponse:
        items, _last_seen_at = await self._repository.list_rankings()
        # With data we surface "now" so the dashboard reflects a live, DB-backed ranking.
        return ViralCveRankingResponse(
            items=items,
            last_refreshed_at=datetime.now(UTC) if items else None,
            is_stale=not items,
        )

    async def refresh_rankings(self) -> ViralCveRefreshResponse:
        return ViralCveRefreshResponse(
            rankings=await self.list_rankings(),
            message="Ranking rebuilt from the latest Reddit and Bluesky source data.",
        )


def get_viral_cve_service(session: AsyncSession) -> ViralCveService:
    return ViralCveService(session)
