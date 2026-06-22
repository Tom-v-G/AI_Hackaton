from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from de_lekbak_backend.models.bluesky_mention import BlueskyMention  # noqa: F401  (ensures mapper is registered)
from de_lekbak_backend.repositories.bluesky_mention_repository import (
    BlueskyMentionRepository,
    EnrichedBlueskyCve,
)
from de_lekbak_backend.repositories.reddit_cve_repository import RedditCveRepository
from de_lekbak_backend.schemas.viral_cve import (
    NvdEnrichment,
    SourceLink,
    SourceType,
    ViralCveItem,
)
from de_lekbak_backend.services.scoring import calculate_virality_score


def _max_dt(*values: datetime | None) -> datetime | None:
    present = [value for value in values if value is not None]
    return max(present) if present else None


def _min_dt(*values: datetime | None) -> datetime | None:
    present = [value for value in values if value is not None]
    return min(present) if present else None


def _reddit_link(url: str, observed_at: datetime | None) -> SourceLink:
    host = urlparse(url).netloc or "reddit"
    return SourceLink(source_type=SourceType.reddit, title=host, url=url, observed_at=observed_at)


def _nvd_from_bluesky(enriched: EnrichedBlueskyCve | None) -> NvdEnrichment | None:
    if enriched is None or not enriched.nvd_found:
        return None
    return NvdEnrichment(
        severity=enriched.nvd_severity,
        description=enriched.nvd_description,
        affected_vendors=enriched.affected_vendors,
        affected_products=enriched.affected_products,
        published_at=enriched.nvd_published_at,
        modified_at=enriched.nvd_modified_at,
    )


class ViralCveRepository:
    """Builds the combined viral-CVE ranking from the persisted source tables.

    Mentions are aggregated per CVE across Reddit and Bluesky, scored with
    ``calculate_virality_score`` and enriched with NVD data when available.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._reddit = RedditCveRepository(session)
        self._bluesky = BlueskyMentionRepository(session)

    async def list_rankings(self) -> tuple[list[ViralCveItem], datetime | None]:
        reddit_rows = await self._reddit.list_trending()
        bluesky_rows = await self._bluesky.enriched_cves(limit=100)

        reddit_by_cve = {row.cve_number: row for row in reddit_rows}
        bluesky_by_cve = {row.cve_id: row for row in bluesky_rows}

        items: list[ViralCveItem] = []
        last_seen_overall: datetime | None = None

        for cve_id in reddit_by_cve.keys() | bluesky_by_cve.keys():
            reddit = reddit_by_cve.get(cve_id)
            bluesky = bluesky_by_cve.get(cve_id)

            source_types: list[SourceType] = []
            mention_count = 0
            links: list[SourceLink] = []
            first_seen: datetime | None = None
            last_seen: datetime | None = None

            if reddit is not None:
                source_types.append(SourceType.reddit)
                mention_count += reddit.mention_count
                first_seen = _min_dt(first_seen, reddit.first_seen)
                last_seen = _max_dt(last_seen, reddit.last_seen)
                links.extend(_reddit_link(url, reddit.last_seen) for url in reddit.source_urls())

            if bluesky is not None:
                source_types.append(SourceType.bluesky)
                mention_count += bluesky.mention_count
                last_seen = _max_dt(last_seen, bluesky.latest_mention_at)

            last_seen_overall = _max_dt(last_seen_overall, last_seen)

            items.append(
                ViralCveItem(
                    cve_id=cve_id,
                    virality_score=calculate_virality_score(mention_count, set(source_types)),
                    mention_count=mention_count,
                    distinct_source_count=len(source_types),
                    source_types=source_types,
                    first_seen_at=first_seen,
                    last_seen_at=last_seen,
                    representative_links=links,
                    nvd=_nvd_from_bluesky(bluesky),
                )
            )

        items.sort(
            key=lambda item: (item.virality_score, item.mention_count, item.cve_id),
            reverse=True,
        )
        return items, last_seen_overall
