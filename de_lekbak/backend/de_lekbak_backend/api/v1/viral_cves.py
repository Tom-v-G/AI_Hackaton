from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from de_lekbak_backend.db.session import get_async_session
from de_lekbak_backend.schemas.viral_cve import (
    ViralCveRankingResponse,
    ViralCveRefreshResponse,
)
from de_lekbak_backend.services.viral_cve_service import (
    ViralCveService,
    get_viral_cve_service as build_viral_cve_service,
)

router = APIRouter()


async def get_viral_cve_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ViralCveService:
    return build_viral_cve_service(session)


@router.get("", response_model=ViralCveRankingResponse)
async def list_viral_cves(
    service: Annotated[ViralCveService, Depends(get_viral_cve_service)],
) -> ViralCveRankingResponse:
    return await service.list_rankings()


@router.post("/refresh", response_model=ViralCveRefreshResponse)
async def refresh_viral_cves(
    service: Annotated[ViralCveService, Depends(get_viral_cve_service)],
) -> ViralCveRefreshResponse:
    return await service.refresh_rankings()
