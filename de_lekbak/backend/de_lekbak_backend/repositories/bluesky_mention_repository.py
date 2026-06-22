from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import case, desc, distinct, func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from de_lekbak_backend.models.bluesky_mention import BlueskyMention


@dataclass(frozen=True)
class BlueskyMentionInput:
    post_uri: str
    cid: str | None
    author_did: str | None
    author_handle: str | None
    display_name: str | None
    created_at: datetime
    indexed_at: datetime
    text: str
    like_count: int
    reply_count: int
    repost_count: int
    quote_count: int
    engagement_score: float
    extracted_cves: list[str]


@dataclass(frozen=True)
class EnrichedBlueskyCve:
    cve_id: str
    mention_count: int
    latest_mention_at: datetime | None
    top_engagement_score: float
    nvd_found: bool
    nvd_severity: str | None
    nvd_base_score: float | None
    nvd_description: str | None
    nvd_published_at: datetime | None
    nvd_modified_at: datetime | None
    affected_vendors: list[str]
    affected_products: list[str]


class BlueskyMentionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_mention(self, mention: BlueskyMentionInput) -> None:
        statement = self.build_upsert_statement(mention)
        await self._session.execute(statement)

    def build_upsert_statement(self, mention: BlueskyMentionInput):  # noqa: ANN201
        statement = insert(BlueskyMention).values(**asdict(mention))
        excluded = statement.excluded
        return statement.on_conflict_do_update(
            index_elements=[BlueskyMention.post_uri],
            set_={
                "cid": excluded.cid,
                "author_did": excluded.author_did,
                "author_handle": excluded.author_handle,
                "display_name": excluded.display_name,
                "created_at": excluded.created_at,
                "indexed_at": excluded.indexed_at,
                "text": case(
                    (BlueskyMention.text.is_distinct_from(excluded.text), excluded.text),
                    else_=BlueskyMention.text,
                ),
                "like_count": excluded.like_count,
                "reply_count": excluded.reply_count,
                "repost_count": excluded.repost_count,
                "quote_count": excluded.quote_count,
                "engagement_score": excluded.engagement_score,
                "extracted_cves": excluded.extracted_cves,
            },
            where=BlueskyMention.text.is_distinct_from(excluded.text)
            | (BlueskyMention.like_count != excluded.like_count)
            | (BlueskyMention.reply_count != excluded.reply_count)
            | (BlueskyMention.repost_count != excluded.repost_count)
            | (BlueskyMention.quote_count != excluded.quote_count)
            | (BlueskyMention.engagement_score != excluded.engagement_score)
            | (BlueskyMention.indexed_at != excluded.indexed_at),
        )

    async def trending_cves_last_24_hours(self, limit: int = 10) -> list[tuple[str, int]]:
        rows = (
            await self._session.execute(self.build_trending_cves_last_24_hours_query(limit))
        ).all()
        return [(row.cve, row.mention_count) for row in rows]

    def build_trending_cves_last_24_hours_query(self, limit: int = 10):  # noqa: ANN201
        cve = func.unnest(BlueskyMention.extracted_cves).label("cve")
        return (
            select(cve, func.count(BlueskyMention.id).label("mention_count"))
            .where(BlueskyMention.created_at >= datetime.now(UTC) - timedelta(hours=24))
            .group_by(cve)
            .order_by(desc("mention_count"), cve)
            .limit(limit)
        )

    async def top_posts_by_engagement(self, limit: int = 10) -> list[BlueskyMention]:
        statement = (
            select(BlueskyMention).order_by(BlueskyMention.engagement_score.desc()).limit(limit)
        )
        return list((await self._session.scalars(statement)).all())

    async def unique_post_count_per_cve(self) -> list[tuple[str, int]]:
        rows = (await self._session.execute(self.build_unique_post_count_per_cve_query())).all()
        return [(row.cve, row.post_count) for row in rows]

    def build_unique_post_count_per_cve_query(self):  # noqa: ANN201
        cve = func.unnest(BlueskyMention.extracted_cves).label("cve")
        return (
            select(cve, func.count(distinct(BlueskyMention.post_uri)).label("post_count"))
            .group_by(cve)
            .order_by(desc("post_count"), cve)
        )

    async def most_active_authors(self, limit: int = 10) -> list[tuple[str, int]]:
        rows = (await self._session.execute(self.build_most_active_authors_query(limit))).all()
        return [(row.author_handle, row.post_count) for row in rows]

    def build_most_active_authors_query(self, limit: int = 10):  # noqa: ANN201
        return (
            select(
                BlueskyMention.author_handle,
                func.count(BlueskyMention.id).label("post_count"),
            )
            .where(BlueskyMention.author_handle.is_not(None))
            .group_by(BlueskyMention.author_handle)
            .order_by(desc("post_count"), BlueskyMention.author_handle)
            .limit(limit)
        )

    async def enriched_cves(self, limit: int = 25) -> list[EnrichedBlueskyCve]:
        rows = (await self._session.execute(self.build_enriched_cves_query(limit))).mappings().all()
        return [
            EnrichedBlueskyCve(
                cve_id=str(row["cve_id"]),
                mention_count=int(row["mention_count"]),
                latest_mention_at=row["latest_mention_at"],
                top_engagement_score=float(row["top_engagement_score"] or 0),
                nvd_found=bool(row["nvd_found"]),
                nvd_severity=row["nvd_severity"],
                nvd_base_score=float(row["nvd_base_score"])
                if row["nvd_base_score"] is not None
                else None,
                nvd_description=row["nvd_description"],
                nvd_published_at=row["nvd_published_at"],
                nvd_modified_at=row["nvd_modified_at"],
                affected_vendors=list(row["affected_vendors"] or []),
                affected_products=list(row["affected_products"] or []),
            )
            for row in rows
        ]

    def build_enriched_cves_query(self, limit: int = 25):  # noqa: ANN201
        return text(
            """
            WITH mentioned_cves AS (
                SELECT
                    unnest(extracted_cves) AS cve_id,
                    count(*) AS mention_count,
                    max(indexed_at) AS latest_mention_at,
                    max(engagement_score) AS top_engagement_score
                FROM bluesky_mentions
                GROUP BY cve_id
            ), best_metrics AS (
                SELECT DISTINCT ON (cve_id)
                    cve_id,
                    base_severity,
                    base_score
                FROM cve_metrics
                ORDER BY cve_id, base_score DESC NULLS LAST
            )
            SELECT
                mentioned_cves.cve_id,
                mentioned_cves.mention_count,
                mentioned_cves.latest_mention_at,
                mentioned_cves.top_engagement_score,
                cves.id IS NOT NULL AS nvd_found,
                best_metrics.base_severity AS nvd_severity,
                best_metrics.base_score AS nvd_base_score,
                cves.description_en AS nvd_description,
                cves.published_at AS nvd_published_at,
                cves.last_modified AS nvd_modified_at,
                coalesce(cves.affected_vendors, ARRAY[]::text[]) AS affected_vendors,
                coalesce(cves.affected_products, ARRAY[]::text[]) AS affected_products
            FROM mentioned_cves
            LEFT JOIN cves ON cves.cve_id = mentioned_cves.cve_id
            LEFT JOIN best_metrics ON best_metrics.cve_id = cves.id
            ORDER BY
                mentioned_cves.mention_count DESC,
                mentioned_cves.top_engagement_score DESC,
                mentioned_cves.latest_mention_at DESC
            LIMIT :limit
            """
        ).bindparams(limit=limit)
