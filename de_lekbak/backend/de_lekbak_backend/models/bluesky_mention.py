import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from de_lekbak_backend.db.base import Base


class BlueskyMention(Base):
    __tablename__ = "bluesky_mentions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    post_uri: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    cid: Mapped[str | None] = mapped_column(String(256))
    author_did: Mapped[str | None] = mapped_column(String(256))
    author_handle: Mapped[str | None] = mapped_column(String(256))
    display_name: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reply_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    repost_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quote_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    engagement_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    extracted_cves: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    inserted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


Index("ix_bluesky_mentions_created_at", BlueskyMention.created_at)
Index("ix_bluesky_mentions_author_handle", BlueskyMention.author_handle)
Index(
    "ix_bluesky_mentions_extracted_cves",
    BlueskyMention.extracted_cves,
    postgresql_using="gin",
)
Index(
    "ix_bluesky_mentions_engagement_score_desc",
    BlueskyMention.engagement_score.desc(),
)
