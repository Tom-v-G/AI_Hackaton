import ast
from pathlib import Path

from fastapi.testclient import TestClient

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


def test_backend_does_not_import_cve_intelligence() -> None:
    package_root = Path(__file__).resolve().parents[1] / "de_lekbak_backend"
    for python_file in package_root.rglob("*.py"):
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
