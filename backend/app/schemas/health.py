from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str


class ReadinessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    database: bool
    migrations_applied: bool
    initialized: bool


class VersionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application: str
    version: str
    api_version: str
    demo_mode: bool
    git_commit: str | None = None
    build_date: str | None = None


class RuntimeSettingsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ffprobe_path: str
    ffprobe_timeout: int
    mkvpropedit_path: str
    metadata_edit_enabled: bool
    scan_concurrency: int
    scheduled_scan_enabled: bool
    scheduled_scan_interval_minutes: int
    stale_retention_days: int
    timezone: str
