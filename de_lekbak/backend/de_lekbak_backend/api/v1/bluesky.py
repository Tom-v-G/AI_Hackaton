from typing import Annotated

from fastapi import APIRouter, Depends, Query

from de_lekbak_backend.schemas.bluesky import (
    BlueskyActiveAuthorsResponse,
    BlueskyCvePostCountsResponse,
    BlueskyEnrichedCvesResponse,
    BlueskyTopPostsResponse,
    BlueskyTrendingCvesResponse,
)
from de_lekbak_backend.services.bluesky_analytics_service import (
    BlueskyAnalyticsService,
    get_bluesky_analytics_service,
)

router = APIRouter()
bluesky_analytics_service_dependency = Depends(get_bluesky_analytics_service)
LimitQuery = Annotated[int, Query(ge=1, le=100)]


@router.get("/trending-cves", response_model=BlueskyTrendingCvesResponse)
async def list_trending_cves(
    limit: LimitQuery = 10,
    service: BlueskyAnalyticsService = bluesky_analytics_service_dependency,
) -> BlueskyTrendingCvesResponse:
    return await service.trending_cves(limit)


@router.get("/top-posts", response_model=BlueskyTopPostsResponse)
async def list_top_posts(
    limit: LimitQuery = 10,
    service: BlueskyAnalyticsService = bluesky_analytics_service_dependency,
) -> BlueskyTopPostsResponse:
    return await service.top_posts(limit)


@router.get("/cve-post-counts", response_model=BlueskyCvePostCountsResponse)
async def list_cve_post_counts(
    service: BlueskyAnalyticsService = bluesky_analytics_service_dependency,
) -> BlueskyCvePostCountsResponse:
    return await service.cve_post_counts()


@router.get("/active-authors", response_model=BlueskyActiveAuthorsResponse)
async def list_active_authors(
    limit: LimitQuery = 10,
    service: BlueskyAnalyticsService = bluesky_analytics_service_dependency,
) -> BlueskyActiveAuthorsResponse:
    return await service.active_authors(limit)


@router.get("/enriched-cves", response_model=BlueskyEnrichedCvesResponse)
async def list_enriched_cves(
    limit: LimitQuery = 25,
    service: BlueskyAnalyticsService = bluesky_analytics_service_dependency,
) -> BlueskyEnrichedCvesResponse:
    return await service.enriched_cves(limit)
