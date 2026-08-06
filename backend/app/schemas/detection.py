from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CzechDetectionSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language_codes: list[str] = Field(min_length=1, max_length=50)
    title_indicators: list[str] = Field(min_length=1, max_length=100)


class CzechDetectionPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: str | None = Field(default=None, max_length=120)
    title: str | None = Field(default=None, max_length=500)
    settings: CzechDetectionSettings | None = None


class CzechDetectionPreviewResponse(BaseModel):
    czech_match: bool
    match_reason: str
    matched_value: str | None
