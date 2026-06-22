import contextlib
import logging
import re
from collections.abc import AsyncIterator, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from de_lekbak_backend.repositories.reddit_cve_repository import RedditCveRepository

logger = logging.getLogger(__name__)

CVE_PATTERN = re.compile(r"\bCVE-(\d{4})-(\d{4,})\b", re.IGNORECASE)
REDDIT_BASE_URL = "https://www.reddit.com"


@dataclass(frozen=True)
class RedditPost:
    canonical_url: str
    created_at: datetime
    title: str
    selftext: str

    @property
    def searchable_text(self) -> str:
        return f"{self.title}\n{self.selftext}"


@dataclass
class RedditCveAggregate:
    cve_number: str
    mention_count: int = 0
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    sources: list[str] = field(default_factory=list)
    _seen_sources: set[str] = field(default_factory=set, repr=False)

    def add_post(self, post: RedditPost) -> None:
        if post.canonical_url in self._seen_sources:
            return
        self._seen_sources.add(post.canonical_url)
        self.sources.append(post.canonical_url)
        self.mention_count += 1
        if self.first_seen is None or post.created_at < self.first_seen:
            self.first_seen = post.created_at
        if self.last_seen is None or post.created_at > self.last_seen:
            self.last_seen = post.created_at


class RedditScraper:
    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        repository: RedditCveRepository | None = None,
        base_url: str = REDDIT_BASE_URL,
        timeout_seconds: float = 10.0,
        user_agent: str = "de-lekbak-reddit-cve-scraper/0.1",
        forbidden_fallback_posts: Iterable[RedditPost] | None = None,
    ) -> None:
        self._client = client
        self._repository = repository
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._user_agent = user_agent
        self._forbidden_fallback_posts = list(forbidden_fallback_posts or [])

    async def scrape(self, subreddits: Iterable[str]) -> list[RedditCveAggregate]:
        cutoff = datetime.now(UTC) - timedelta(days=7)
        aggregates: dict[str, RedditCveAggregate] = {}
        seen_post_urls: set[str] = set()

        async with self._client_context() as client:
            for subreddit in normalize_subreddit_names(subreddits):
                posts = await self._fetch_subreddit_posts(client, subreddit)
                for post in posts:
                    if post.created_at < cutoff or post.canonical_url in seen_post_urls:
                        continue
                    seen_post_urls.add(post.canonical_url)
                    for cve_number in extract_cve_ids(post.searchable_text):
                        aggregate = aggregates.setdefault(
                            cve_number, RedditCveAggregate(cve_number=cve_number)
                        )
                        aggregate.add_post(post)

        return [aggregate for aggregate in aggregates.values() if aggregate.mention_count > 0]

    async def scrape_and_persist(self, subreddits: Iterable[str]) -> list[RedditCveAggregate]:
        aggregates = await self.scrape(subreddits)
        if self._repository is not None:
            await self._repository.upsert_many(aggregates)
        return aggregates

    def _client_context(self) -> contextlib.AbstractAsyncContextManager[httpx.AsyncClient]:
        if self._client is not None:
            return _borrowed_async_client(self._client)
        return httpx.AsyncClient(
            timeout=self._timeout_seconds,
            headers={"User-Agent": self._user_agent},
            follow_redirects=True,
        )

    async def _fetch_subreddit_posts(
        self, client: httpx.AsyncClient, subreddit: str
    ) -> list[RedditPost]:
        try:
            response = await client.get(
                f"{self._base_url}/r/{subreddit}/new.json",
                params={"limit": 100},
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 403 and self._forbidden_fallback_posts:
                logger.warning(
                    "Using fallback Reddit posts for subreddit %s after 403 response", subreddit
                )
                return list(self._forbidden_fallback_posts)
            logger.warning("Skipping subreddit %s after Reddit fetch failure: %s", subreddit, exc)
            return []
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Skipping subreddit %s after Reddit fetch failure: %s", subreddit, exc)
            return []

        children = payload.get("data", {}).get("children", []) if isinstance(payload, dict) else []
        if not isinstance(children, list):
            logger.warning("Skipping subreddit %s after malformed Reddit response", subreddit)
            return []

        posts: list[RedditPost] = []
        for child in children:
            post = parse_reddit_child(child, self._base_url)
            if post is not None:
                posts.append(post)
        return posts


@contextlib.asynccontextmanager
async def _borrowed_async_client(client: httpx.AsyncClient) -> AsyncIterator[httpx.AsyncClient]:
    yield client


def extract_cve_ids(text: str) -> set[str]:
    return {
        f"CVE-{match.group(1)}-{match.group(2)}".upper()
        for match in CVE_PATTERN.finditer(text)
    }


def normalize_subreddit_name(value: str) -> str:
    normalized = value.strip().strip("/")
    if normalized.lower().startswith("r/"):
        normalized = normalized[2:]
    return normalized.strip("/")


def normalize_subreddit_names(values: Iterable[str]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = normalize_subreddit_name(value)
        key = normalized.lower()
        if normalized and key not in seen:
            names.append(normalized)
            seen.add(key)
    return names


def parse_reddit_child(child: object, base_url: str = REDDIT_BASE_URL) -> RedditPost | None:
    if not isinstance(child, Mapping):
        return None
    data = child.get("data")
    if not isinstance(data, Mapping):
        return None

    permalink = _string_value(data, "permalink")
    created_utc = data.get("created_utc")
    if permalink is None or not isinstance(created_utc, int | float):
        return None

    return RedditPost(
        canonical_url=canonical_reddit_url(permalink, base_url),
        created_at=datetime.fromtimestamp(float(created_utc), UTC),
        title=_string_value(data, "title") or "",
        selftext=_string_value(data, "selftext") or "",
    )


def canonical_reddit_url(permalink: str, base_url: str = REDDIT_BASE_URL) -> str:
    if permalink.startswith("http://") or permalink.startswith("https://"):
        path = httpx.URL(permalink).path
    else:
        path = permalink
    canonical_path = "/" + path.strip("/") + "/"
    return f"{base_url.rstrip('/')}{canonical_path}"


def _string_value(data: Mapping[str, Any], key: str) -> str | None:
    value = data.get(key)
    return value if isinstance(value, str) else None
