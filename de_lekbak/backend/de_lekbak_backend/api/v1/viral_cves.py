from fastapi import APIRouter, Depends

from de_lekbak_backend.schemas.viral_cve import (
    ViralCveRankingResponse,
    ViralCveRefreshResponse,
)
from de_lekbak_backend.services.viral_cve_service import (
    ViralCveService,
    get_viral_cve_service,
)

router = APIRouter()
viral_cve_service_dependency = Depends(get_viral_cve_service)


@router.get("", response_model=ViralCveRankingResponse)
async def list_viral_cves(
    service: ViralCveService = viral_cve_service_dependency,
) -> ViralCveRankingResponse:
    return service.list_rankings()


@router.post("/refresh", response_model=ViralCveRefreshResponse)
async def refresh_viral_cves(
    service: ViralCveService = viral_cve_service_dependency,
) -> ViralCveRefreshResponse:
    return service.refresh_rankings()
