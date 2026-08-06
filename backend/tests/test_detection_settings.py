from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.session import SessionLocal, initialize_database
from app.main import create_app
from app.models.setting import ApplicationSetting
from app.services.detection_settings import (
    DETECTION_SETTINGS_KEY,
    default_detection_settings,
    detection_settings_version,
    save_detection_settings,
)


def _clear_detection_settings() -> None:
    with SessionLocal() as session:
        setting = session.get(ApplicationSetting, DETECTION_SETTINGS_KEY)
        if setting is not None:
            session.delete(setting)
            session.commit()


def test_detection_settings_preview_and_reset() -> None:
    initialize_database()
    _clear_detection_settings()
    try:
        with TestClient(create_app()) as client:
            default_response = client.get("/api/v1/czech-detection-settings")
            update_response = client.put(
                "/api/v1/czech-detection-settings",
                json={
                    "language_codes": ["cs", "custom-cz"],
                    "title_indicators": ["cesky dabing", "custom title"],
                },
            )
            preview_response = client.post(
                "/api/v1/czech-detection-settings/preview",
                json={"language": "custom-cz", "title": None, "settings": None},
            )
            reset_response = client.post("/api/v1/czech-detection-settings/reset")

        assert default_response.status_code == 200
        assert "cs" in default_response.json()["language_codes"]
        assert update_response.status_code == 200
        assert update_response.json()["language_codes"] == ["cs", "custom-cz"]
        assert preview_response.status_code == 200
        assert preview_response.json()["czech_match"] is True
        assert preview_response.json()["match_reason"] == "custom_language_code"
        assert reset_response.status_code == 200
        assert reset_response.json() == default_detection_settings().model_dump(mode="json")
    finally:
        _clear_detection_settings()


def test_detection_settings_version_changes_with_configuration() -> None:
    initialize_database()
    _clear_detection_settings()
    try:
        default_settings = default_detection_settings()
        with SessionLocal() as session:
            custom_settings = save_detection_settings(
                session,
                default_settings.model_copy(
                    update={"language_codes": [*default_settings.language_codes, "x-cz"]}
                ),
            )

        assert detection_settings_version(default_settings) != detection_settings_version(
            custom_settings
        )
    finally:
        _clear_detection_settings()
