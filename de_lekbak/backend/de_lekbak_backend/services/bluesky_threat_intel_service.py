import re
from dataclasses import dataclass

from de_lekbak_backend.core.config import Settings, get_settings
from de_lekbak_backend.repositories.bluesky_mention_repository import (
    BlueskyMentionInput,
    BlueskyMentionRepository,
)
from de_lekbak_backend.services.threat_intel import (
    BlueskySearchProvider,
    ThreatIntelPost,
    ThreatIntelProvider,
)

CVE_PATTERN = re.compile(r"CVE-\d{4}-\d+", re.IGNORECASE)


@dataclass(frozen=True)
class BlueskyIngestionResult:
    fetched_posts: int
    persisted_posts: int


class BlueskyThreatIntelService:
    def __init__(
        self,
        repository: BlueskyMentionRepository,
        provider: ThreatIntelProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._provider = provider or BlueskySearchProvider()
        self._settings = settings or get_settings()

    async def ingest_latest(self) -> BlueskyIngestionResult:
        if not self._settings.bluesky_enabled:
            return BlueskyIngestionResult(fetched_posts=0, persisted_posts=0)

        posts = await self._provider.fetch_posts(self._settings.bluesky_search_terms)
        persisted = 0
        for post in posts:
            cves = self.extract_cves(post.text)
            if not cves:
                continue
            await self._repository.upsert_mention(self._to_mention_input(post, cves))
            persisted += 1
        return BlueskyIngestionResult(fetched_posts=len(posts), persisted_posts=persisted)

    def extract_cves(self, text: str) -> list[str]:
        return sorted({match.upper() for match in CVE_PATTERN.findall(text)})

    def calculate_engagement_score(self, post: ThreatIntelPost) -> float:
        return (
            post.like_count * self._settings.bluesky_like_weight
            + post.reply_count * self._settings.bluesky_reply_weight
            + post.repost_count * self._settings.bluesky_repost_weight
            + post.quote_count * self._settings.bluesky_quote_weight
        )

    def _to_mention_input(self, post: ThreatIntelPost, cves: list[str]) -> BlueskyMentionInput:
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
            engagement_score=self.calculate_engagement_score(post),
            extracted_cves=cves,
        )
