from fastapi.testclient import TestClient

from app.db.session import SessionLocal, initialize_database
from app.main import create_app
from app.models.integration import Integration


def clear_integrations() -> None:
    initialize_database()
    with SessionLocal() as session:
        session.query(Integration).delete()
        session.commit()


def test_create_integration_does_not_return_api_key() -> None:
    clear_integrations()
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/integrations",
            json={
                "source_type": "radarr",
                "name": "Main Radarr",
                "base_url": "https://radarr.example.test/",
                "api_key": "secret-key",
                "timeout_seconds": 10,
                "verify_tls": True,
                "enabled": True,
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["base_url"] == "https://radarr.example.test"
    assert payload["api_key_configured"] is True
    assert "api_key" not in payload


def test_list_integrations_returns_secret_safe_state() -> None:
    clear_integrations()
    with TestClient(create_app()) as client:
        client.post(
            "/api/v1/integrations",
            json={
                "source_type": "sonarr",
                "name": "Main Sonarr",
                "base_url": "https://sonarr.example.test",
                "api_key": "secret-key",
            },
        )
        response = client.get("/api/v1/integrations")

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["source_type"] == "sonarr"
    assert payload[0]["api_key_configured"] is True
    assert "secret-key" not in response.text
