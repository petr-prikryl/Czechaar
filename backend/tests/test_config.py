from pathlib import Path

from app.core.config import Settings


def test_sqlite_database_url_defaults_to_config_directory() -> None:
    settings = Settings(config_dir=Path("config"))

    assert settings.resolved_database_url == "sqlite:///config/czecharr.db"
    assert settings.is_sqlite is True


def test_explicit_database_url_wins() -> None:
    settings = Settings(database_url="sqlite:////tmp/custom.db")

    assert settings.resolved_database_url == "sqlite:////tmp/custom.db"
