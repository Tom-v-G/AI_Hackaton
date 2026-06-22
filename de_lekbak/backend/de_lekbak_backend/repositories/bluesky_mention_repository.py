from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

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
    nvd_source_identifier: str | None
    nvd_vuln_status: str | None
    nvd_severity: str | None
    nvd_base_score: float | None
    nvd_vector_string: str | None
    nvd_metric_type: str | None
    nvd_description: str | None
    nvd_published_at: datetime | None
    nvd_modified_at: datetime | None
    nvd_ingested_at: datetime | None
    nvd_created_at: datetime | None
    nvd_updated_at: datetime | None
    nvd_cwe_ids: list[str]
    affected_vendors: list[str]
    affected_products: list[str]
    nvd_references: list[dict[str, Any]]
    nvd_metrics: list[dict[str, Any]]
    raw_nvd: dict[str, Any] | None


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

    async def enriched_cves(
        self,
        limit: int = 25,
        *,
        nvd_only: bool = False,
    ) -> list[EnrichedBlueskyCve]:
        rows = (
            await self._session.execute(self.build_enriched_cves_query(limit, nvd_only=nvd_only))
        ).mappings().all()
        return [
            EnrichedBlueskyCve(
                cve_id=str(row["cve_id"]),
                mention_count=int(row["mention_count"]),
                latest_mention_at=row["latest_mention_at"],
                top_engagement_score=float(row["top_engagement_score"] or 0),
                nvd_found=bool(row["nvd_found"]),
                nvd_source_identifier=row["nvd_source_identifier"],
                nvd_vuln_status=row["nvd_vuln_status"],
                nvd_severity=row["nvd_severity"],
                nvd_base_score=float(row["nvd_base_score"])
                if row["nvd_base_score"] is not None
                else None,
                nvd_vector_string=row["nvd_vector_string"],
                nvd_metric_type=row["nvd_metric_type"],
                nvd_description=row["nvd_description"],
                nvd_published_at=row["nvd_published_at"],
                nvd_modified_at=row["nvd_modified_at"],
                nvd_ingested_at=row["nvd_ingested_at"],
                nvd_created_at=row["nvd_created_at"],
                nvd_updated_at=row["nvd_updated_at"],
                nvd_cwe_ids=list(row["nvd_cwe_ids"] or []),
                affected_vendors=list(row["affected_vendors"] or []),
                affected_products=list(row["affected_products"] or []),
                nvd_references=list(row["nvd_references"] or []),
                nvd_metrics=list(row["nvd_metrics"] or []),
                raw_nvd=row["raw_nvd"],
            )
            for row in rows
        ]

    def build_enriched_cves_query(self, limit: int = 25, *, nvd_only: bool = False):  # noqa: ANN201
        where_clause = "WHERE cves.id IS NOT NULL" if nvd_only else ""
        return text(
            f"""
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
                    base_score,
                    vector_string,
                    metric_type
                FROM cve_metrics
                ORDER BY cve_id, base_score DESC NULLS LAST
            ), metric_details AS (
                SELECT
                    cve_id,
                    jsonb_agg(
                        jsonb_build_object(
                            'version', version,
                            'source', source,
                            'metric_type', metric_type,
                            'base_score', base_score,
                            'base_severity', base_severity,
                            'vector_string', vector_string,
                            'raw_metric', raw_metric
                        )
                        ORDER BY base_score DESC NULLS LAST, version DESC, metric_type
                    ) AS metrics
                FROM cve_metrics
                GROUP BY cve_id
            ), reference_details AS (
                SELECT
                    cve_id,
                    jsonb_agg(
                        jsonb_build_object(
                            'url', url,
                            'source', source,
                            'tags', coalesce(tags, ARRAY[]::text[])
                        )
                        ORDER BY url
                    ) AS refs
                FROM cve_references
                GROUP BY cve_id
            )
            SELECT
                mentioned_cves.cve_id,
                mentioned_cves.mention_count,
                mentioned_cves.latest_mention_at,
                mentioned_cves.top_engagement_score,
                cves.id IS NOT NULL AS nvd_found,
                cves.source_identifier AS nvd_source_identifier,
                cves.vuln_status AS nvd_vuln_status,
                best_metrics.base_severity AS nvd_severity,
                best_metrics.base_score AS nvd_base_score,
                best_metrics.vector_string AS nvd_vector_string,
                best_metrics.metric_type AS nvd_metric_type,
                cves.description_en AS nvd_description,
                cves.published_at AS nvd_published_at,
                cves.last_modified AS nvd_modified_at,
                cves.ingested_at AS nvd_ingested_at,
                cves.created_at AS nvd_created_at,
                cves.updated_at AS nvd_updated_at,
                coalesce(cves.cwe_ids, ARRAY[]::text[]) AS nvd_cwe_ids,
                coalesce(cves.affected_vendors, ARRAY[]::text[]) AS affected_vendors,
                coalesce(cves.affected_products, ARRAY[]::text[]) AS affected_products,
                coalesce(reference_details.refs, '[]'::jsonb) AS nvd_references,
                coalesce(metric_details.metrics, '[]'::jsonb) AS nvd_metrics,
                cves.raw_nvd AS raw_nvd
            FROM mentioned_cves
            LEFT JOIN cves ON cves.cve_id = mentioned_cves.cve_id
            LEFT JOIN best_metrics ON best_metrics.cve_id = cves.id
            LEFT JOIN metric_details ON metric_details.cve_id = cves.id
            LEFT JOIN reference_details ON reference_details.cve_id = cves.id
            {where_clause}
            ORDER BY
                nvd_found DESC,
                mentioned_cves.mention_count DESC,
                mentioned_cves.top_engagement_score DESC,
                mentioned_cves.latest_mention_at DESC
            LIMIT :limit
            """
        ).bindparams(limit=limit)
