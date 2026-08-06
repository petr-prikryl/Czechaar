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
    git_commit: str | None = None
    build_date: str | None = None
