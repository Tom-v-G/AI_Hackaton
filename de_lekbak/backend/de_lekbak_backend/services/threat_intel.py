from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

import httpx


@dataclass(frozen=True)
class ThreatIntelPost:
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


class ThreatIntelProvider(Protocol):
    async def fetch_posts(self, search_terms: Sequence[str]) -> list[ThreatIntelPost]: ...


class BlueskySearchProvider:
    endpoint = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def fetch_posts(self, search_terms: Sequence[str]) -> list[ThreatIntelPost]:
        if self._client is not None:
            return await self._fetch_with_client(self._client, search_terms)

        async with httpx.AsyncClient() as client:
            return await self._fetch_with_client(client, search_terms)

    async def _fetch_with_client(
        self, client: httpx.AsyncClient, search_terms: Sequence[str]
    ) -> list[ThreatIntelPost]:
        posts: list[ThreatIntelPost] = []
        for term in search_terms:
            response = await client.get(self.endpoint, params={"q": term, "sort": "latest"})
            response.raise_for_status()
            posts.extend(self._parse_response(response.json()))
        return posts

    def _parse_response(self, payload: dict[str, object]) -> list[ThreatIntelPost]:
        raw_posts = payload.get("posts", [])
        if not isinstance(raw_posts, list):
            return []
        return [post for item in raw_posts if (post := self._parse_post(item)) is not None]

    def _parse_post(self, item: object) -> ThreatIntelPost | None:
        if not isinstance(item, dict):
            return None
        uri = item.get("uri")
        record = item.get("record")
        if not isinstance(uri, str) or not isinstance(record, dict):
            return None
        text = record.get("text")
        created_at = self._parse_datetime(record.get("createdAt"))
        indexed_at = self._parse_datetime(item.get("indexedAt")) or datetime.now(UTC)
        if not isinstance(text, str) or created_at is None:
            return None
        author = item.get("author")
        if not isinstance(author, dict):
            author = {}
        return ThreatIntelPost(
            post_uri=uri,
            cid=item.get("cid") if isinstance(item.get("cid"), str) else None,
            author_did=author.get("did") if isinstance(author.get("did"), str) else None,
            author_handle=author.get("handle") if isinstance(author.get("handle"), str) else None,
            display_name=author.get("displayName")
            if isinstance(author.get("displayName"), str)
            else None,
            created_at=created_at,
            indexed_at=indexed_at,
            text=text,
            like_count=self._parse_count(item.get("likeCount")),
            reply_count=self._parse_count(item.get("replyCount")),
            repost_count=self._parse_count(item.get("repostCount")),
            quote_count=self._parse_count(item.get("quoteCount")),
        )

    def _parse_count(self, value: object) -> int:
        return value if isinstance(value, int) else 0

    def _parse_datetime(self, value: object) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
