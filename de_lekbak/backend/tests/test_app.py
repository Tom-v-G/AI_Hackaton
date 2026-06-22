import ast
import asyncio
import uuid
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from de_lekbak_backend.api.v1.reddit import get_reddit_service
from de_lekbak_backend.core.config import Settings
from de_lekbak_backend.db import models  # noqa: F401
from de_lekbak_backend.db import session as db_session
from de_lekbak_backend.db.base import Base
from de_lekbak_backend.main import create_app
from de_lekbak_backend.models.bluesky_mention import BlueskyMention
from de_lekbak_backend.repositories.bluesky_mention_repository import (
    BlueskyMentionInput,
    BlueskyMentionRepository,
    EnrichedBlueskyCve,
)
from de_lekbak_backend.schemas.reddit import RedditCveEntry, RedditTrendingResponse
from de_lekbak_backend.services.bluesky_analytics_service import get_bluesky_analytics_service
from de_lekbak_backend.services.bluesky_threat_intel_service import BlueskyThreatIntelService
from de_lekbak_backend.services.threat_intel import BlueskySearchProvider, ThreatIntelPost


def test_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "de-lekbak-backend"}


def test_viral_rankings_are_available_without_nvd_data() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/viral-cves")

    body = response.json()

    assert response.status_code == 200
    assert body["items"] == []
    assert body["is_stale"] is True


def test_refresh_endpoint_marks_data_fresh() -> None:
    client = TestClient(create_app())


    response = client.post("/api/v1/viral-cves/refresh")
    body = response.json()

    assert response.status_code == 200
    assert body["rankings"]["items"] == []
    assert body["rankings"]["is_stale"] is False
    assert body["rankings"]["last_refreshed_at"] is not None


def test_bluesky_dashboard_endpoints_return_repository_backed_data() -> None:
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

    class FakeBlueskyAnalyticsService:
        async def trending_cves(self, limit: int = 10) -> BlueskyTrendingCvesResponse:
            assert limit == 5
            return BlueskyTrendingCvesResponse(
                items=[BlueskyTrendingCveItem(cve_id="CVE-2026-1234", mention_count=3)]
            )

        async def top_posts(self, limit: int = 10) -> BlueskyTopPostsResponse:
            assert limit == 2
            observed_at = datetime(2026, 6, 22, tzinfo=UTC)
            return BlueskyTopPostsResponse(
                items=[
                    BlueskyTopPostItem(
                        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        post_uri="at://did:example/app.bsky.feed.post/1",
                        cid="cid-1",
                        author_did="did:example",
                        author_handle="alice.test",
                        display_name="Alice",
                        created_at=observed_at,
                        indexed_at=observed_at,
                        text="CVE-2026-1234 exploit",
                        like_count=1,
                        reply_count=2,
                        repost_count=3,
                        quote_count=4,
                        engagement_score=16.0,
                        extracted_cves=["CVE-2026-1234"],
                        inserted_at=observed_at,
                    )
                ]
            )

        async def cve_post_counts(self) -> BlueskyCvePostCountsResponse:
            return BlueskyCvePostCountsResponse(
                items=[BlueskyCvePostCountItem(cve_id="CVE-2026-1234", post_count=2)]
            )

        async def active_authors(self, limit: int = 10) -> BlueskyActiveAuthorsResponse:
            assert limit == 4
            return BlueskyActiveAuthorsResponse(
                items=[BlueskyActiveAuthorItem(author_handle="alice.test", post_count=7)]
            )

        async def enriched_cves(
            self,
            limit: int = 25,
            *,
            nvd_only: bool = False,
        ) -> BlueskyEnrichedCvesResponse:
            assert limit == 6
            assert nvd_only is True
            observed_at = datetime(2026, 6, 22, tzinfo=UTC)
            return BlueskyEnrichedCvesResponse(
                items=[
                    BlueskyEnrichedCveItem(
                        cve_id="CVE-2026-1234",
                        mention_count=3,
                        latest_mention_at=observed_at,
                        top_engagement_score=16.0,
                        nvd=BlueskyNvdEnrichment(
                            found=True,
                            severity="CRITICAL",
                            base_score=9.8,
                            description="Remote code execution",
                            published_at=observed_at,
                            modified_at=observed_at,
                            affected_vendors=["Example"],
                            affected_products=["Widget"],
                        ),
                    )
                ]
            )

    app = create_app()
    app.dependency_overrides[get_bluesky_analytics_service] = FakeBlueskyAnalyticsService
    client = TestClient(app)

    trending = client.get("/api/v1/bluesky/trending-cves?limit=5")
    top_posts = client.get("/api/v1/bluesky/top-posts?limit=2")
    counts = client.get("/api/v1/bluesky/cve-post-counts")
    authors = client.get("/api/v1/bluesky/active-authors?limit=4")
    enriched = client.get("/api/v1/bluesky/enriched-cves?limit=6&nvd_only=true")

    assert trending.status_code == 200
    assert trending.json()["items"] == [{"cve_id": "CVE-2026-1234", "mention_count": 3}]
    assert top_posts.status_code == 200
    assert top_posts.json()["items"][0]["author_handle"] == "alice.test"
    assert top_posts.json()["items"][0]["extracted_cves"] == ["CVE-2026-1234"]
    assert counts.status_code == 200
    assert counts.json()["items"] == [{"cve_id": "CVE-2026-1234", "post_count": 2}]
    assert authors.status_code == 200
    assert authors.json()["items"] == [{"author_handle": "alice.test", "post_count": 7}]
    assert enriched.status_code == 200
    assert enriched.json()["items"][0]["cve_id"] == "CVE-2026-1234"
    assert enriched.json()["items"][0]["nvd"]["found"] is True
    assert enriched.json()["items"][0]["nvd"]["severity"] == "CRITICAL"


def test_bluesky_dashboard_endpoint_limits_are_validated() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/bluesky/trending-cves?limit=0")

    assert response.status_code == 422


def test_reddit_trending_endpoint_refreshes_and_returns_database_entries() -> None:
    app = create_app()
    observed_subreddits: list[str] = []
    now = datetime(2026, 6, 22, tzinfo=UTC)

    class StubRedditService:
        async def refresh_trending(self, subreddits: list[str]) -> RedditTrendingResponse:
            observed_subreddits.extend(subreddits)
            return RedditTrendingResponse(
                items=[
                    RedditCveEntry(
                        id=UUID("00000000-0000-0000-0000-000000000001"),
                        cve_number="CVE-2026-1234",
                        mention_count=3,
                        first_seen=now,
                        last_seen=now,
                        sources=["https://www.reddit.com/r/netsec/comments/abc/post/"],
                        created_at=now,
                        updated_at=now,
                    )
                ]
            )

    app.dependency_overrides[get_reddit_service] = StubRedditService
    client = TestClient(app)

    response = client.get("/api/v1/reddit/trending?subreddits=netsec&subreddits=cybersecurity")
    body = response.json()

    assert response.status_code == 200
    assert observed_subreddits == ["netsec", "cybersecurity"]
    assert body["items"] == [
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "cve_number": "CVE-2026-1234",
            "mention_count": 3,
            "first_seen": "2026-06-22T00:00:00Z",
            "last_seen": "2026-06-22T00:00:00Z",
            "sources": ["https://www.reddit.com/r/netsec/comments/abc/post/"],
            "created_at": "2026-06-22T00:00:00Z",
            "updated_at": "2026-06-22T00:00:00Z",
        }
    ]


def test_database_settings_use_de_lekbak_env_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DE_LEKBAK_DATABASE_URL",
        "postgresql+asyncpg://lekbak:secret@db.example.test:5432/lekbak_test",
    )
    monkeypatch.setenv("DE_LEKBAK_DATABASE_POOL_SIZE", "7")
    monkeypatch.setenv("DE_LEKBAK_DATABASE_MAX_OVERFLOW", "3")
    monkeypatch.setenv("DE_LEKBAK_DATABASE_ECHO", "true")

    settings = Settings()

    assert str(settings.database_url).startswith(
        "postgresql+asyncpg://lekbak:secret@db.example.test:5432/lekbak_test"
    )
    assert settings.database_pool_size == 7
    assert settings.database_max_overflow == 3
    assert settings.database_echo is True


def test_database_settings_defaults_are_postgres_async() -> None:
    settings = Settings()

    assert str(settings.database_url).startswith("postgresql+asyncpg://")
    assert settings.database_pool_size == 5
    assert settings.database_max_overflow == 10
    assert settings.database_echo is False


def test_bluesky_settings_use_de_lekbak_env_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DE_LEKBAK_BLUESKY_ENABLED", "false")
    monkeypatch.setenv("DE_LEKBAK_BLUESKY_POLL_INTERVAL_SECONDS", "123")
    monkeypatch.setenv("DE_LEKBAK_BLUESKY_SEARCH_TERMS", "CVE,critical vulnerability,RCE")
    monkeypatch.setenv("DE_LEKBAK_BLUESKY_LIKE_WEIGHT", "2")
    monkeypatch.setenv("DE_LEKBAK_BLUESKY_REPLY_WEIGHT", "3")
    monkeypatch.setenv("DE_LEKBAK_BLUESKY_REPOST_WEIGHT", "4")
    monkeypatch.setenv("DE_LEKBAK_BLUESKY_QUOTE_WEIGHT", "5")

    settings = Settings()

    assert settings.bluesky_enabled is False
    assert settings.bluesky_poll_interval_seconds == 123
    assert settings.bluesky_search_terms == ["CVE", "critical vulnerability", "RCE"]
    assert settings.bluesky_like_weight == 2
    assert settings.bluesky_reply_weight == 3
    assert settings.bluesky_repost_weight == 4
    assert settings.bluesky_quote_weight == 5


def test_orm_base_metadata_is_available_for_alembic() -> None:
    assert "reddit_cves" in Base.metadata.tables
    assert Base.metadata.tables["bluesky_mentions"] is BlueskyMention.__table__


def test_bluesky_cve_extraction_handles_multiple_and_empty_posts() -> None:
    service = BlueskyThreatIntelService(repository=None)  # type: ignore[arg-type]

    assert service.extract_cves("CVE-2024-1234 and cve-2025-99999") == [
        "CVE-2024-1234",
        "CVE-2025-99999",
    ]
    assert service.extract_cves("no vulnerability id here") == []


def test_bluesky_engagement_score_uses_configurable_weights() -> None:
    service = BlueskyThreatIntelService(
        repository=None,  # type: ignore[arg-type]
        settings=Settings(
            bluesky_like_weight=2,
            bluesky_reply_weight=3,
            bluesky_repost_weight=4,
            bluesky_quote_weight=5,
        ),
    )
    post = _post(like_count=1, reply_count=2, repost_count=3, quote_count=4)

    assert service.calculate_engagement_score(post) == 40


def test_bluesky_provider_requests_latest_sort_and_parses_posts() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "posts": [
                    {
                        "uri": "at://did:example/app.bsky.feed.post/1",
                        "cid": "cid-1",
                        "author": {
                            "did": "did:example",
                            "handle": "alice.test",
                            "displayName": "Alice",
                        },
                        "record": {
                            "text": "CVE-2024-1234 exploit",
                            "createdAt": "2026-06-22T10:00:00Z",
                        },
                        "indexedAt": "2026-06-22T10:01:00Z",
                        "likeCount": 1,
                        "replyCount": 2,
                        "repostCount": 3,
                        "quoteCount": 4,
                    }
                ]
            },
        )

    async def exercise() -> list[ThreatIntelPost]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await BlueskySearchProvider(client).fetch_posts(["CVE"])

    posts = asyncio.run(exercise())

    assert requests[0].url.params["q"] == "CVE"
    assert requests[0].url.params["sort"] == "latest"
    assert posts[0].post_uri == "at://did:example/app.bsky.feed.post/1"
    assert posts[0].author_handle == "alice.test"
    assert posts[0].like_count == 1


def test_bluesky_service_persists_only_posts_with_cves() -> None:
    class Provider:
        async def fetch_posts(self, search_terms: list[str]) -> list[ThreatIntelPost]:
            assert search_terms == ["CVE"]
            return [_post(text="CVE-2024-1234"), _post(post_uri="at://post/2", text="nothing")]

    class Repository:
        mentions: list[BlueskyMentionInput]

        def __init__(self) -> None:
            self.mentions = []

        async def upsert_mention(self, mention: BlueskyMentionInput) -> None:
            self.mentions.append(mention)

    repository = Repository()
    service = BlueskyThreatIntelService(
        repository=repository,  # type: ignore[arg-type]
        provider=Provider(),  # type: ignore[arg-type]
        settings=Settings(bluesky_search_terms=["CVE"]),
    )

    result = asyncio.run(service.ingest_latest())

    assert result.fetched_posts == 2
    assert result.persisted_posts == 1
    assert repository.mentions[0].extracted_cves == ["CVE-2024-1234"]


def test_bluesky_repository_builds_post_uri_upsert_for_counts_text_and_cves() -> None:
    repository = BlueskyMentionRepository(session=None)  # type: ignore[arg-type]

    compiled = str(
        repository.build_upsert_statement(_mention()).compile(dialect=postgresql.dialect())
    )

    assert "ON CONFLICT (post_uri) DO UPDATE" in compiled
    assert "like_count" in compiled
    assert "reply_count" in compiled
    assert "repost_count" in compiled
    assert "quote_count" in compiled
    assert "engagement_score" in compiled
    assert "indexed_at" in compiled
    assert "extracted_cves" in compiled


def test_bluesky_repository_analytics_queries_reference_required_dimensions() -> None:
    repository = BlueskyMentionRepository(session=None)  # type: ignore[arg-type]

    trending = str(
        repository.build_trending_cves_last_24_hours_query().compile(dialect=postgresql.dialect())
    )
    unique_counts = str(
        repository.build_unique_post_count_per_cve_query().compile(dialect=postgresql.dialect())
    )
    authors = str(
        repository.build_most_active_authors_query().compile(dialect=postgresql.dialect())
    )
    enriched = str(repository.build_enriched_cves_query().compile(dialect=postgresql.dialect()))
    enriched_nvd_only = str(
        repository.build_enriched_cves_query(nvd_only=True).compile(dialect=postgresql.dialect())
    )

    assert "unnest" in trending
    assert "created_at" in trending
    assert "count(DISTINCT" in unique_counts
    assert "author_handle" in authors
    assert "LEFT JOIN cves" in enriched
    assert "LEFT JOIN best_metrics" in enriched
    assert "LEFT JOIN metric_details" in enriched
    assert "LEFT JOIN reference_details" in enriched
    assert "description_en" in enriched
    assert "raw_nvd" in enriched
    assert "WHERE cves.id IS NOT NULL" in enriched_nvd_only


def test_bluesky_analytics_service_maps_nvd_enrichment() -> None:
    class Repository:
        async def enriched_cves(
            self,
            limit: int = 25,
            *,
            nvd_only: bool = False,
        ) -> list[EnrichedBlueskyCve]:
            assert limit == 1
            assert nvd_only is True
            observed_at = datetime(2026, 6, 22, tzinfo=UTC)
            return [
                EnrichedBlueskyCve(
                    cve_id="CVE-2026-1234",
                    mention_count=2,
                    latest_mention_at=observed_at,
                    top_engagement_score=10.0,
                    nvd_found=True,
                    nvd_source_identifier="nvd@nist.gov",
                    nvd_vuln_status="Analyzed",
                    nvd_severity="HIGH",
                    nvd_base_score=8.1,
                    nvd_vector_string="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    nvd_metric_type="primary",
                    nvd_description="Example vulnerability",
                    nvd_published_at=observed_at,
                    nvd_modified_at=observed_at,
                    nvd_ingested_at=observed_at,
                    nvd_created_at=observed_at,
                    nvd_updated_at=observed_at,
                    nvd_cwe_ids=["CWE-79"],
                    affected_vendors=["Example"],
                    affected_products=["Product"],
                    nvd_references=[{"url": "https://example.test", "source": "NVD", "tags": []}],
                    nvd_metrics=[{"version": "3.1", "base_score": 8.1}],
                    raw_nvd={"id": "CVE-2026-1234"},
                )
            ]

    from de_lekbak_backend.services.bluesky_analytics_service import BlueskyAnalyticsService

    response = asyncio.run(
        BlueskyAnalyticsService(Repository()).enriched_cves(1, nvd_only=True)  # type: ignore[arg-type]
    )

    assert response.items[0].cve_id == "CVE-2026-1234"
    assert response.items[0].nvd.found is True
    assert response.items[0].nvd.base_score == 8.1
    assert response.items[0].nvd.cwe_ids == ["CWE-79"]
    assert response.items[0].nvd.references[0]["url"] == "https://example.test"
    assert response.items[0].nvd.metrics[0]["version"] == "3.1"
    assert response.items[0].nvd.raw_nvd == {"id": "CVE-2026-1234"}


def test_async_session_dependency_commits_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    sessions: list[AsyncSession] = []

    class TrackingAsyncSession(AsyncSession):
        committed = False
        rolled_back = False

        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, **kwargs)
            sessions.append(self)

        async def commit(self) -> None:
            self.committed = True

        async def rollback(self) -> None:
            self.rolled_back = True

    factory = async_sessionmaker(class_=TrackingAsyncSession, expire_on_commit=False)
    monkeypatch.setattr(db_session, "_async_session_factory", factory)

    async def exercise_dependency() -> None:
        generator = db_session.get_async_session()
        yielded_session = await anext(generator)
        assert isinstance(yielded_session, AsyncSession)
        with pytest.raises(StopAsyncIteration):
            await anext(generator)

    asyncio.run(exercise_dependency())

    assert sessions[0].committed is True
    assert sessions[0].rolled_back is False


def test_async_session_dependency_rolls_back_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    sessions: list[AsyncSession] = []

    class TrackingAsyncSession(AsyncSession):
        committed = False
        rolled_back = False

        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, **kwargs)
            sessions.append(self)

        async def commit(self) -> None:
            self.committed = True

        async def rollback(self) -> None:
            self.rolled_back = True

    factory = async_sessionmaker(class_=TrackingAsyncSession, expire_on_commit=False)
    monkeypatch.setattr(db_session, "_async_session_factory", factory)

    async def exercise_dependency() -> None:
        generator = db_session.get_async_session()
        await anext(generator)
        with pytest.raises(RuntimeError, match="boom"):
            await generator.athrow(RuntimeError("boom"))

    asyncio.run(exercise_dependency())

    assert sessions[0].committed is False
    assert sessions[0].rolled_back is True


def test_backend_does_not_import_cve_intelligence() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    checked_roots = [backend_root / "de_lekbak_backend", backend_root / "alembic"]
    for python_file in [path for root in checked_roots for path in root.rglob("*.py")]:
        tree = ast.parse(python_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported_names = [node.module or ""]
            else:
                continue

            assert all(not name.startswith("cve_intelligence") for name in imported_names)
            assert all(not name.startswith("app") for name in imported_names)


def _post(
    post_uri: str = "at://post/1",
    text: str = "CVE-2024-1234",
    like_count: int = 0,
    reply_count: int = 0,
    repost_count: int = 0,
    quote_count: int = 0,
) -> ThreatIntelPost:
    timestamp = datetime(2026, 6, 22, tzinfo=UTC)
    return ThreatIntelPost(
        post_uri=post_uri,
        cid="cid-1",
        author_did="did:example",
        author_handle="alice.test",
        display_name="Alice",
        created_at=timestamp,
        indexed_at=timestamp,
        text=text,
        like_count=like_count,
        reply_count=reply_count,
        repost_count=repost_count,
        quote_count=quote_count,
    )


def _mention() -> BlueskyMentionInput:
    post = _post(like_count=1, reply_count=2, repost_count=3, quote_count=4)
    return BlueskyMentionInput(
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
        engagement_score=18.0,
        extracted_cves=["CVE-2024-1234"],
    )
