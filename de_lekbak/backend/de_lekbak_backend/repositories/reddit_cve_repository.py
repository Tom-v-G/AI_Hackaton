from collections.abc import Iterable
from datetime import datetime
from typing import Protocol

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from de_lekbak_backend.db.models import RedditCve


class RedditCveRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_many(self, aggregates: Iterable["RedditCveAggregateLike"]) -> None:
        for aggregate in aggregates:
            statement = insert(RedditCve).values(
                cve_number=aggregate.cve_number,
                mention_count=aggregate.mention_count,
                first_seen=aggregate.first_seen,
                last_seen=aggregate.last_seen,
                sources=aggregate.sources,
            )
            update_statement = statement.on_conflict_do_update(
                index_elements=[RedditCve.cve_number],
                set_={
                    "mention_count": statement.excluded.mention_count,
                    "first_seen": statement.excluded.first_seen,
                    "last_seen": statement.excluded.last_seen,
                    "sources": statement.excluded.sources,
                },
            )
            await self._session.execute(update_statement)


class RedditCveAggregateLike(Protocol):
    cve_number: str
    mention_count: int
    first_seen: datetime | None
    last_seen: datetime | None
    sources: list[str]
