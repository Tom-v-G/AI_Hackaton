from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from de_lekbak_backend.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RedditCve(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reddit_cves"

    cve_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    mention_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sources: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    def source_urls(self) -> list[str]:
        return [source for source in self.sources if isinstance(source, str)]
