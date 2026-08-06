from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CZECHARR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Czecharr"
    config_dir: Path = Path("config")
    database_url: str | None = None
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "INFO"
    ffprobe_path: str = "ffprobe"
    ffprobe_timeout: int = 60
    scan_concurrency: int = 2
    scheduled_scan_enabled: bool = False
    scheduled_scan_interval_minutes: int = 1440
    demo_mode: bool = False
    static_dir: Path | None = None
    timezone: str = Field(
        default="Europe/Prague", validation_alias=AliasChoices("TZ", "CZECHARR_TIMEZONE")
    )
    git_commit: str | None = None
    build_date: str | None = None

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        database_path = self.config_dir / "czecharr.db"
        return f"sqlite:///{database_path.as_posix()}"

    @property
    def is_sqlite(self) -> bool:
        return self.resolved_database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
