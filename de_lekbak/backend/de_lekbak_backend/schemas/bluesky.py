import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BlueskyTrendingCveItem(BaseModel):
    cve_id: str
    mention_count: int


class BlueskyTrendingCvesResponse(BaseModel):
    items: list[BlueskyTrendingCveItem]


class BlueskyTopPostItem(BaseModel):
    id: uuid.UUID
    post_uri: str
    cid: str | None = None
    author_did: str | None = None
    author_handle: str | None = None
    display_name: str | None = None
    created_at: datetime
    indexed_at: datetime
    text: str
    like_count: int
    reply_count: int
    repost_count: int
    quote_count: int
    engagement_score: float
    extracted_cves: list[str] = Field(default_factory=list)
    inserted_at: datetime


class BlueskyTopPostsResponse(BaseModel):
    items: list[BlueskyTopPostItem]


class BlueskyCvePostCountItem(BaseModel):
    cve_id: str
    post_count: int


class BlueskyCvePostCountsResponse(BaseModel):
    items: list[BlueskyCvePostCountItem]


class BlueskyActiveAuthorItem(BaseModel):
    author_handle: str
    post_count: int


class BlueskyActiveAuthorsResponse(BaseModel):
    items: list[BlueskyActiveAuthorItem]


class BlueskyNvdEnrichment(BaseModel):
    found: bool
    severity: str | None = None
    base_score: float | None = None
    description: str | None = None
    published_at: datetime | None = None
    modified_at: datetime | None = None
    affected_vendors: list[str] = Field(default_factory=list)
    affected_products: list[str] = Field(default_factory=list)


class BlueskyEnrichedCveItem(BaseModel):
    cve_id: str
    mention_count: int
    latest_mention_at: datetime | None = None
    top_engagement_score: float
    nvd: BlueskyNvdEnrichment


class BlueskyEnrichedCvesResponse(BaseModel):
    items: list[BlueskyEnrichedCveItem]
