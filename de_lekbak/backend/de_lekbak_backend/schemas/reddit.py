from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RedditCveEntry(BaseModel):
    id: UUID
    cve_number: str
    mention_count: int
    first_seen: datetime
    last_seen: datetime
    sources: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RedditTrendingResponse(BaseModel):
    items: list[RedditCveEntry]
