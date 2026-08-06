from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.url import UrlValidationError, normalize_base_url
from app.models.enums import SourceType


class IntegrationBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: SourceType
    name: str = Field(min_length=1, max_length=120)
    base_url: str = Field(min_length=1, max_length=500)
    enabled: bool = True
    timeout_seconds: float = Field(default=30.0, ge=1.0, le=300.0)
    verify_tls: bool = True
    api_key_env_var: str | None = Field(default=None, max_length=120)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        try:
            return normalize_base_url(value)
        except UrlValidationError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("api_key_env_var")
    @classmethod
    def validate_env_var(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if not value.replace("_", "").isalnum() or value[0].isdigit():
            raise ValueError("Environment variable name is invalid.")
        return value


class IntegrationCreate(IntegrationBase):
    api_key: str | None = Field(default=None, max_length=500)


class IntegrationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    base_url: str | None = Field(default=None, min_length=1, max_length=500)
    enabled: bool | None = None
    timeout_seconds: float | None = Field(default=None, ge=1.0, le=300.0)
    verify_tls: bool | None = None
    api_key: str | None = Field(default=None, max_length=500)
    api_key_env_var: str | None = Field(default=None, max_length=120)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return normalize_base_url(value)
        except UrlValidationError as exc:
            raise ValueError(str(exc)) from exc


class IntegrationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_type: SourceType
    name: str
    base_url: str
    enabled: bool
    timeout_seconds: float
    verify_tls: bool
    api_key_env_var: str | None
    api_key_configured: bool
    last_test_at: datetime | None
    created_at: datetime
    updated_at: datetime


class IntegrationConnectionTestRequest(IntegrationCreate):
    pass


class IntegrationConnectionTestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    status_code: int | None = None
    error_code: str | None = None
    message: str
    application: str | None = None
    version: str | None = None
