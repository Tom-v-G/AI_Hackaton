import ast
import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from de_lekbak_backend.core.config import Settings
from de_lekbak_backend.db import session as db_session
from de_lekbak_backend.db.base import Base
from de_lekbak_backend.main import create_app


def test_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "de-lekbak-backend"}


def test_viral_rankings_are_available_without_nvd_data() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/viral-cves")

    body = response.json()

    assert response.status_code == 200
    assert body["items"] == []
    assert body["is_stale"] is True


def test_refresh_endpoint_marks_data_fresh() -> None:
    client = TestClient(create_app())


    response = client.post("/api/v1/viral-cves/refresh")
    body = response.json()

    assert response.status_code == 200
    assert body["rankings"]["items"] == []
    assert body["rankings"]["is_stale"] is False
    assert body["rankings"]["last_refreshed_at"] is not None


def test_database_settings_use_de_lekbak_env_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DE_LEKBAK_DATABASE_URL",
        "postgresql+asyncpg://lekbak:secret@db.example.test:5432/lekbak_test",
    )
    monkeypatch.setenv("DE_LEKBAK_DATABASE_POOL_SIZE", "7")
    monkeypatch.setenv("DE_LEKBAK_DATABASE_MAX_OVERFLOW", "3")
    monkeypatch.setenv("DE_LEKBAK_DATABASE_ECHO", "true")

    settings = Settings()

    assert str(settings.database_url).startswith(
        "postgresql+asyncpg://lekbak:secret@db.example.test:5432/lekbak_test"
    )
    assert settings.database_pool_size == 7
    assert settings.database_max_overflow == 3
    assert settings.database_echo is True


def test_database_settings_defaults_are_postgres_async() -> None:
    settings = Settings()

    assert str(settings.database_url).startswith("postgresql+asyncpg://")
    assert settings.database_pool_size == 5
    assert settings.database_max_overflow == 10
    assert settings.database_echo is False


def test_orm_base_metadata_is_available_for_alembic() -> None:
    assert Base.metadata.tables == {}


def test_async_session_dependency_commits_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    sessions: list[AsyncSession] = []

    class TrackingAsyncSession(AsyncSession):
        committed = False
        rolled_back = False

        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, **kwargs)
            sessions.append(self)

        async def commit(self) -> None:
            self.committed = True

        async def rollback(self) -> None:
            self.rolled_back = True

    factory = async_sessionmaker(class_=TrackingAsyncSession, expire_on_commit=False)
    monkeypatch.setattr(db_session, "_async_session_factory", factory)

    async def exercise_dependency() -> None:
        generator = db_session.get_async_session()
        yielded_session = await anext(generator)
        assert isinstance(yielded_session, AsyncSession)
        with pytest.raises(StopAsyncIteration):
            await anext(generator)

    asyncio.run(exercise_dependency())

    assert sessions[0].committed is True
    assert sessions[0].rolled_back is False


def test_async_session_dependency_rolls_back_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    sessions: list[AsyncSession] = []

    class TrackingAsyncSession(AsyncSession):
        committed = False
        rolled_back = False

        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, **kwargs)
            sessions.append(self)

        async def commit(self) -> None:
            self.committed = True

        async def rollback(self) -> None:
            self.rolled_back = True

    factory = async_sessionmaker(class_=TrackingAsyncSession, expire_on_commit=False)
    monkeypatch.setattr(db_session, "_async_session_factory", factory)

    async def exercise_dependency() -> None:
        generator = db_session.get_async_session()
        await anext(generator)
        with pytest.raises(RuntimeError, match="boom"):
            await generator.athrow(RuntimeError("boom"))

    asyncio.run(exercise_dependency())

    assert sessions[0].committed is False
    assert sessions[0].rolled_back is True


def test_backend_does_not_import_cve_intelligence() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    checked_roots = [backend_root / "de_lekbak_backend", backend_root / "alembic"]
    for python_file in [path for root in checked_roots for path in root.rglob("*.py")]:
        tree = ast.parse(python_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported_names = [node.module or ""]
            else:
                continue

            assert all(not name.startswith("cve_intelligence") for name in imported_names)
            assert all(not name.startswith("app") for name in imported_names)
