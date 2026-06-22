from datetime import UTC, datetime

from de_lekbak_backend.schemas.viral_cve import ViralCveItem


class ViralCveRepository:
    """Temporary in-memory repository until source ingestion persistence is added."""

    def __init__(self) -> None:
        self._items: list[ViralCveItem] = []
        self._last_refreshed_at: datetime | None = None

    def list_rankings(self) -> tuple[list[ViralCveItem], datetime | None]:
        return self._items, self._last_refreshed_at

    def mark_refreshed(self) -> datetime:
        self._last_refreshed_at = datetime.now(UTC)
        return self._last_refreshed_at


repository = ViralCveRepository()
