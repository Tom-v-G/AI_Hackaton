from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from de_lekbak_backend.db.session import get_async_session
from de_lekbak_backend.models.bluesky_mention import BlueskyMention
from de_lekbak_backend.repositories.bluesky_mention_repository import BlueskyMentionRepository
from de_lekbak_backend.schemas.bluesky import (
    BlueskyActiveAuthorItem,
    BlueskyActiveAuthorsResponse,
    BlueskyCvePostCountItem,
    BlueskyCvePostCountsResponse,
    BlueskyEnrichedCveItem,
    BlueskyEnrichedCvesResponse,
    BlueskyNvdEnrichment,
    BlueskyTopPostItem,
    BlueskyTopPostsResponse,
    BlueskyTrendingCveItem,
    BlueskyTrendingCvesResponse,
)

async_session_dependency = Depends(get_async_session)


class BlueskyAnalyticsService:
    def __init__(self, repository: BlueskyMentionRepository) -> None:
        self._repository = repository

    async def trending_cves(self, limit: int = 10) -> BlueskyTrendingCvesResponse:
        rows = await self._repository.trending_cves_last_24_hours(limit)
        return BlueskyTrendingCvesResponse(
            items=[
                BlueskyTrendingCveItem(cve_id=cve_id, mention_count=mention_count)
                for cve_id, mention_count in rows
            ]
        )

    async def top_posts(self, limit: int = 10) -> BlueskyTopPostsResponse:
        posts = await self._repository.top_posts_by_engagement(limit)
        return BlueskyTopPostsResponse(items=[_post_to_schema(post) for post in posts])

    async def cve_post_counts(self) -> BlueskyCvePostCountsResponse:
        rows = await self._repository.unique_post_count_per_cve()
        return BlueskyCvePostCountsResponse(
            items=[
                BlueskyCvePostCountItem(cve_id=cve_id, post_count=post_count)
                for cve_id, post_count in rows
            ]
        )

    async def active_authors(self, limit: int = 10) -> BlueskyActiveAuthorsResponse:
        rows = await self._repository.most_active_authors(limit)
        return BlueskyActiveAuthorsResponse(
            items=[
                BlueskyActiveAuthorItem(author_handle=author_handle, post_count=post_count)
                for author_handle, post_count in rows
            ]
        )

    async def enriched_cves(
        self,
        limit: int = 25,
        *,
        nvd_only: bool = False,
    ) -> BlueskyEnrichedCvesResponse:
        rows = await self._repository.enriched_cves(limit, nvd_only=nvd_only)
        return BlueskyEnrichedCvesResponse(
            items=[
                BlueskyEnrichedCveItem(
                    cve_id=row.cve_id,
                    mention_count=row.mention_count,
                    latest_mention_at=row.latest_mention_at,
                    top_engagement_score=row.top_engagement_score,
                    nvd=BlueskyNvdEnrichment(
                        found=row.nvd_found,
                        source_identifier=row.nvd_source_identifier,
                        vuln_status=row.nvd_vuln_status,
                        severity=row.nvd_severity,
                        base_score=row.nvd_base_score,
                        vector_string=row.nvd_vector_string,
                        metric_type=row.nvd_metric_type,
                        description=row.nvd_description,
                        published_at=row.nvd_published_at,
                        modified_at=row.nvd_modified_at,
                        ingested_at=row.nvd_ingested_at,
                        created_at=row.nvd_created_at,
                        updated_at=row.nvd_updated_at,
                        cwe_ids=row.nvd_cwe_ids,
                        affected_vendors=row.affected_vendors,
                        affected_products=row.affected_products,
                        references=row.nvd_references,
                        metrics=row.nvd_metrics,
                        raw_nvd=row.raw_nvd,
                    ),
                )
                for row in rows
            ]
        )


async def get_bluesky_analytics_service(
    session: AsyncSession = async_session_dependency,
) -> BlueskyAnalyticsService:
    return BlueskyAnalyticsService(BlueskyMentionRepository(session))


def _post_to_schema(post: BlueskyMention) -> BlueskyTopPostItem:
    return BlueskyTopPostItem(
        id=post.id,
        post_uri=post.post_uri,
        cid=post.cid,
        author_did=post.author_did,
        author_handle=post.author_handle,
        display_name=post.display_name,
        created_at=post.created_at,
        indexed_at=post.indexed_at,
        text=post.text,
        like_count=post.like_count,
        reply_count=post.reply_count,
        repost_count=post.repost_count,
        quote_count=post.quote_count,
        engagement_score=post.engagement_score,
        extracted_cves=post.extracted_cves,
        inserted_at=post.inserted_at,
    )
