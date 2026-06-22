from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    reddit = "reddit"
    mastodon = "mastodon"
    hacker_news = "hacker_news"


class SourceLink(BaseModel):
    source_type: SourceType
    title: str
    url: str
    observed_at: datetime | None = None


class NvdEnrichment(BaseModel):
    severity: str | None = None
    description: str | None = None
    affected_vendors: list[str] = Field(default_factory=list)
    affected_products: list[str] = Field(default_factory=list)
    published_at: datetime | None = None
    modified_at: datetime | None = None


class ViralCveItem(BaseModel):
    cve_id: str
    virality_score: float
    mention_count: int
    distinct_source_count: int
    source_types: list[SourceType]
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    representative_links: list[SourceLink] = Field(default_factory=list)
    nvd: NvdEnrichment | None = None


class ViralCveRankingResponse(BaseModel):
    items: list[ViralCveItem]
    last_refreshed_at: datetime | None = None
    is_stale: bool = False


class ViralCveRefreshResponse(BaseModel):
    rankings: ViralCveRankingResponse
    message: str

