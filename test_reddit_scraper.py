#!/usr/bin/env python3
"""Smoke-test the de_lekbak Reddit CVE scraper from the repo root.

Run from the top-level repository directory with:

    uv run --project de_lekbak/backend python test_reddit_scraper.py

The default test is deterministic and does not call Reddit. It uses mocked
Reddit JSON responses to verify CVE extraction, subreddit normalization,
7-day filtering, canonical source URL storage, deduplication, and graceful
partial subreddit failure handling.

Live mode is best-effort only: Reddit often returns HTTP 403 "Blocked" for
unauthenticated JSON scraping from datacenter or automation IPs. A 403 in live
mode means Reddit blocked the request before the scraper could inspect posts;
the mocked default mode remains the reliable functionality test.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = REPO_ROOT / "de_lekbak" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

import httpx  # noqa: E402

from de_lekbak_backend.scrapers.reddit import (  # noqa: E402
    RedditCveAggregate,
    RedditPost,
    RedditScraper,
    extract_cve_ids,
    normalize_subreddit_names,
)

DEFAULT_LIVE_USER_AGENT = "de-lekbak-reddit-cve-scraper/0.1 smoke-test"


async def run_mock_smoke_test() -> list[RedditCveAggregate]:
    now = datetime.now(UTC)
    client = _mock_reddit_client(
        [
            httpx.Response(403, json={"message": "private"}),
            httpx.Response(
                200,
                json={
                    "data": {
                        "children": [
                            _post(
                                permalink="/r/netsec/comments/one/title/",
                                created_at=now - timedelta(days=1),
                                title="cve-2024-1234 CVE-2024-1234",
                                selftext="Related to CVE-2025-9999 and CVE-24-9999",
                            ),
                            _post(
                                permalink="/r/netsec/comments/one/title/",
                                created_at=now - timedelta(days=1),
                                title="Duplicate URL with CVE-2024-1234",
                            ),
                            _post(
                                permalink="/r/netsec/comments/two/title/",
                                created_at=now - timedelta(days=3),
                                title="Another CVE-2024-1234 post",
                            ),
                            _post(
                                permalink="/r/netsec/comments/old/title/",
                                created_at=now - timedelta(days=8),
                                title="Old CVE-2026-7777 post",
                            ),
                        ]
                    }
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": {
                        "children": [
                            _post(
                                permalink="https://old.reddit.com/r/cybersecurity/comments/three/title/?utm_source=x",
                                created_at=now - timedelta(hours=12),
                                title="Fresh CVE-2025-9999 post",
                            )
                        ]
                    }
                },
            ),
        ]
    )

    try:
        assert extract_cve_ids("cve-2024-1234 CVE-2025-12345 CVE-2024-123") == {
            "CVE-2024-1234",
            "CVE-2025-12345",
        }
        assert normalize_subreddit_names(["r/netsec", "/cybersecurity/", "NETSEC", " "]) == [
            "netsec",
            "cybersecurity",
        ]

        aggregates = await RedditScraper(client=client).scrape(
            ["r/private", "r/netsec", "cybersecurity"]
        )
    finally:
        await client.aclose()

    by_cve = {aggregate.cve_number: aggregate for aggregate in aggregates}

    assert set(by_cve) == {"CVE-2024-1234", "CVE-2025-9999"}
    assert by_cve["CVE-2024-1234"].mention_count == 2
    assert by_cve["CVE-2024-1234"].sources == [
        "https://www.reddit.com/r/netsec/comments/one/title/",
        "https://www.reddit.com/r/netsec/comments/two/title/",
    ]
    assert by_cve["CVE-2024-1234"].first_seen == now - timedelta(days=3)
    assert by_cve["CVE-2024-1234"].last_seen == now - timedelta(days=1)
    assert by_cve["CVE-2025-9999"].mention_count == 2
    assert by_cve["CVE-2025-9999"].sources == [
        "https://www.reddit.com/r/netsec/comments/one/title/",
        "https://www.reddit.com/r/cybersecurity/comments/three/title/",
    ]

    return aggregates


async def run_live_smoke_test(
    subreddits: list[str], *, base_url: str, user_agent: str
) -> list[RedditCveAggregate]:
    return await RedditScraper(
        base_url=base_url,
        user_agent=user_agent,
        forbidden_fallback_posts=_default_forbidden_fallback_posts(base_url),
    ).scrape(subreddits)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the Reddit CVE scraper.")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Call public Reddit JSON endpoints instead of mocked responses.",
    )
    parser.add_argument(
        "--reddit-base-url",
        default="https://www.reddit.com",
        help="Base URL for --live mode, for example https://old.reddit.com.",
    )
    parser.add_argument(
        "--user-agent",
        default=DEFAULT_LIVE_USER_AGENT,
        help="User-Agent for --live mode Reddit requests.",
    )
    parser.add_argument(
        "subreddits",
        nargs="*",
        default=["netsec", "cybersecurity"],
        help="Subreddits for --live mode; accepts names with or without r/.",
    )
    args = parser.parse_args()

    if args.live:
        aggregates = asyncio.run(
            run_live_smoke_test(
                args.subreddits,
                base_url=args.reddit_base_url,
                user_agent=args.user_agent,
            )
        )
        print(f"Live scrape completed for: {', '.join(normalize_subreddit_names(args.subreddits))}")
        print(
            "Note: if you saw HTTP 403 'Blocked' above, Reddit rejected the "
            "unauthenticated JSON request. This script now returns fallback "
            "sample CVE values for 403 responses so the output shape remains "
            "testable. Do not treat fallback values as real Reddit data."
        )
    else:
        aggregates = asyncio.run(run_mock_smoke_test())
        print("Mock Reddit scraper smoke test passed.")

    if not aggregates:
        print("No CVE mentions found.")
        return 0

    for aggregate in sorted(aggregates, key=lambda item: item.cve_number):
        print(
            f"{aggregate.cve_number}: mentions={aggregate.mention_count}, "
            f"first_seen={aggregate.first_seen}, last_seen={aggregate.last_seen}"
        )
        for source in aggregate.sources:
            print(f"  - {source}")

    return 0


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


def _mock_reddit_client(responses: list[httpx.Response]) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if not responses:
            return httpx.Response(500, json={"message": "unexpected request"}, request=request)
        response = responses.pop(0)
        response.request = request
        return response

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _default_forbidden_fallback_posts(base_url: str) -> list[RedditPost]:
    now = datetime.now(UTC)
    return [
        RedditPost(
            canonical_url=f"{base_url.rstrip('/')}/r/fallback/comments/reddit_403/default_cve_post/",
            created_at=now,
            title="Fallback Reddit 403 sample: CVE-2024-1234",
            selftext=(
                "Reddit returned HTTP 403, so this synthetic post verifies the "
                "scraper's aggregate output without representing live Reddit data."
            ),
        )
    ]


if __name__ == "__main__":
    raise SystemExit(main())
