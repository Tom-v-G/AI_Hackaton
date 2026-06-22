from de_lekbak_backend.repositories.viral_cve_repository import repository
from de_lekbak_backend.schemas.viral_cve import ViralCveRankingResponse, ViralCveRefreshResponse


class ViralCveService:
    def list_rankings(self) -> ViralCveRankingResponse:
        items, last_refreshed_at = repository.list_rankings()
        return ViralCveRankingResponse(
            items=items,
            last_refreshed_at=last_refreshed_at,
            is_stale=last_refreshed_at is None,
        )

    def refresh_rankings(self) -> ViralCveRefreshResponse:
        repository.mark_refreshed()
        return ViralCveRefreshResponse(
            rankings=self.list_rankings(),
            message="Refresh completed. Source ingestion is ready to be connected.",
        )


def get_viral_cve_service() -> ViralCveService:
    return ViralCveService()
