from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def test_health_endpoint() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint_checks_database() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["database"] is True
    assert payload["initialized"] is True


def test_version_endpoint() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/version")

    assert response.status_code == 200
    payload = response.json()
    assert payload["application"] == "Czecharr"
    assert payload["api_version"] == "v1"
    assert payload["demo_mode"] is False


def test_runtime_settings_endpoint() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/runtime-settings")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ffprobe_path"] == "ffprobe"
    assert payload["mkvpropedit_path"] == "mkvpropedit"
    assert payload["metadata_edit_enabled"] is False
    assert payload["scan_concurrency"] >= 1
    assert payload["timezone"] == "Europe/Prague"


def test_static_frontend_serves_spa_routes(tmp_path: Path, monkeypatch) -> None:
    dist_dir = tmp_path / "dist"
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir(parents=True)
    (dist_dir / "index.html").write_text("<html><title>Czecharr</title></html>", encoding="utf-8")

    monkeypatch.setenv("CZECHARR_STATIC_DIR", str(dist_dir))
    get_settings.cache_clear()
    try:
        with TestClient(create_app()) as client:
            root_response = client.get("/")
            app_route_response = client.get("/missing-czech-audio")
            api_response = client.get("/api/not-found")
    finally:
        get_settings.cache_clear()

    assert root_response.status_code == 200
    assert "Czecharr" in root_response.text
    assert app_route_response.status_code == 200
    assert "Czecharr" in app_route_response.text
    assert api_response.status_code == 404
