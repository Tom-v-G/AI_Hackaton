import asyncio
from datetime import UTC, datetime, timedelta

import httpx

from de_lekbak_backend.repositories.reddit_cve_repository import RedditCveRepository
from de_lekbak_backend.scrapers.reddit import (
    RedditCveAggregate,
    RedditPost,
    RedditScraper,
    canonical_reddit_url,
    default_reddit_cve_aggregates,
    extract_cve_ids,
    normalize_subreddit_names,
)


def test_extract_cve_ids_normalizes_and_rejects_invalid_ids() -> None:
    cves = extract_cve_ids("cve-2024-1234 CVE-2025-12345 CVE-24-1234 CVE-2024-123")

    assert cves == {"CVE-2024-1234", "CVE-2025-12345"}


def test_normalize_subreddit_names_accepts_r_prefix_and_deduplicates() -> None:
    assert normalize_subreddit_names(["r/netsec", "/cybersecurity/", "NETSEC", " "]) == [
        "netsec",
        "cybersecurity",
    ]


def test_canonical_reddit_url_uses_permalink_path_only() -> None:
    assert (
        canonical_reddit_url("https://old.reddit.com/r/netsec/comments/abc/post/?utm_source=x")
        == "https://www.reddit.com/r/netsec/comments/abc/post/"
    )


def test_reddit_scraper_filters_and_deduplicates_posts() -> None:
    now = datetime.now(UTC)
    payload = {
        "data": {
            "children": [
                _post(
                    permalink="/r/netsec/comments/one/post/",
                    created_at=now - timedelta(days=1),
                    title="CVE-2024-1234 cve-2024-1234",
                    selftext="also CVE-2025-9999",
                ),
                _post(
                    permalink="/r/netsec/comments/one/post/",
                    created_at=now - timedelta(days=1),
                    title="CVE-2024-1234 duplicate url",
                ),
                _post(
                    permalink="/r/netsec/comments/two/post/",
                    created_at=now - timedelta(days=3),
                    title="CVE-2024-1234",
                ),
                _post(
                    permalink="/r/netsec/comments/old/post/",
                    created_at=now - timedelta(days=8),
                    title="CVE-2026-7777",
                ),
            ]
        }
    }
    client = _client_for([httpx.Response(200, json=payload)])

    aggregates = asyncio.run(RedditScraper(client=client).scrape(["netsec"]))
    by_cve = {aggregate.cve_number: aggregate for aggregate in aggregates}

    assert by_cve["CVE-2024-1234"].mention_count == 2
    assert by_cve["CVE-2024-1234"].sources == [
        "https://www.reddit.com/r/netsec/comments/one/post/",
        "https://www.reddit.com/r/netsec/comments/two/post/",
    ]
    assert by_cve["CVE-2024-1234"].first_seen == now - timedelta(days=3)
    assert by_cve["CVE-2024-1234"].last_seen == now - timedelta(days=1)
    assert by_cve["CVE-2025-9999"].mention_count == 1
    assert "CVE-2026-7777" not in by_cve


def test_reddit_scraper_skips_failed_subreddits_and_processes_successes() -> None:
    now = datetime.now(UTC)
    client = _client_for(
        [
            httpx.Response(403, json={"message": "private"}),
            httpx.Response(
                200,
                json={
                    "data": {
                        "children": [
                            _post(
                                permalink="/r/netsec/comments/ok/post/",
                                created_at=now,
                                title="CVE-2024-1111",
                            )
                        ]
                    }
                },
            ),
        ]
    )

    aggregates = asyncio.run(RedditScraper(client=client).scrape(["private", "netsec"]))

    assert [aggregate.cve_number for aggregate in aggregates] == ["CVE-2024-1111"]


def test_reddit_scraper_can_use_fallback_posts_for_forbidden_responses() -> None:
    now = datetime.now(UTC)
    client = _client_for([httpx.Response(403, json={"message": "blocked"})])
    fallback_post = RedditPost(
        canonical_url="https://www.reddit.com/r/netsec/comments/fallback/post/",
        created_at=now,
        title="Fallback CVE-2024-4444",
        selftext="",
    )

    aggregates = asyncio.run(
        RedditScraper(client=client, forbidden_fallback_posts=[fallback_post]).scrape(["netsec"])
    )

    assert [aggregate.cve_number for aggregate in aggregates] == ["CVE-2024-4444"]
    assert aggregates[0].sources == ["https://www.reddit.com/r/netsec/comments/fallback/post/"]


def test_reddit_scraper_persists_with_upsert_repository() -> None:
    now = datetime.now(UTC)
    repository = _RecordingRepository()
    client = _client_for(
        [
            httpx.Response(
                200,
                json={
                    "data": {
                        "children": [
                            _post(
                                permalink="/r/netsec/comments/ok/post/",
                                created_at=now,
                                title="CVE-2024-2222",
                            )
                        ]
                    }
                },
            )
        ]
    )

    aggregates = asyncio.run(
        RedditScraper(client=client, repository=repository).scrape_and_persist(["netsec"])
    )

    assert repository.persisted == aggregates
    assert aggregates[0].sources == ["https://www.reddit.com/r/netsec/comments/ok/post/"]


def test_reddit_scraper_returns_and_persists_defaults_when_scrape_is_empty() -> None:
    repository = _RecordingRepository()
    client = _client_for([httpx.Response(200, json={"data": {"children": []}})])

    aggregates = asyncio.run(
        RedditScraper(client=client, repository=repository).scrape_and_persist(["netsec"])
    )

    assert repository.persisted == aggregates
    assert [aggregate.cve_number for aggregate in aggregates] == [
        "CVE-2026-20245",
        "CVE-2026-20253",
        "CVE-2026-50656",
    ]
    assert all(aggregate.mention_count == 1 for aggregate in aggregates)


def test_default_reddit_cve_aggregates_use_public_advisory_sources() -> None:
    by_cve = {aggregate.cve_number: aggregate for aggregate in default_reddit_cve_aggregates()}

    assert "https://nvd.nist.gov/vuln/detail/CVE-2026-20245" in by_cve[
        "CVE-2026-20245"
    ].sources
    assert any("cisco-sa-sdwan-privesc" in source for source in by_cve["CVE-2026-20245"].sources)
    assert "https://nvd.nist.gov/vuln/detail/CVE-2026-20253" in by_cve[
        "CVE-2026-20253"
    ].sources
    assert "https://advisory.splunk.com/advisories/SVD-2026-0603" in by_cve[
        "CVE-2026-20253"
    ].sources
    assert "https://nvd.nist.gov/vuln/detail/CVE-2026-50656" in by_cve[
        "CVE-2026-50656"
    ].sources
    assert "https://msrc.microsoft.com/update-guide/vulnerability/CVE-2026-50656" in by_cve[
        "CVE-2026-50656"
    ].sources


def test_reddit_cve_repository_uses_upsert_statement() -> None:
    now = datetime.now(UTC)
    session = _RecordingSession()
    repository = RedditCveRepository(session)  # type: ignore[arg-type]
    aggregate = RedditCveAggregate(
        cve_number="CVE-2024-3333",
        mention_count=1,
        first_seen=now,
        last_seen=now,
        sources=["https://www.reddit.com/r/netsec/comments/ok/post/"],
    )

    asyncio.run(repository.upsert_many([aggregate]))

    assert len(session.statements) == 1
    statement_sql = str(session.statements[0])
    assert "ON CONFLICT" in statement_sql
    assert "cve_number" in statement_sql


def _post(
    *, permalink: str, created_at: datetime, title: str = "", selftext: str = ""
) -> dict[str, object]:
    return {
        "data": {
            "permalink": permalink,
            "created_utc": created_at.timestamp(),
            "title": title,
            "selftext": selftext,
        }
    }


def _client_for(responses: list[httpx.Response]) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        response = responses.pop(0)
        response.request = request
        return response

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


class _RecordingRepository:
    def __init__(self) -> None:
        self.persisted: list[object] = []

    async def upsert_many(self, aggregates: list[object]) -> None:
        self.persisted = aggregates


class _RecordingSession:
    def __init__(self) -> None:
        self.statements: list[object] = []

    async def execute(self, statement: object) -> None:
        self.statements.append(statement)
