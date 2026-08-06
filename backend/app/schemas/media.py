from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import MediaType, ScanState, SourceType


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


class MediaFileSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_file_id: str
    original_source_path: str
    mapped_local_path: str | None
    relative_path: str | None
    size: int | None
    quality: str | None
    quality_profile: str | None
    scan_state: ScanState
    czech_audio_result: bool | None
    last_successful_scan: datetime | None
    last_scan_attempt: datetime | None
    error_code: str | None
    sanitized_error_message: str | None
    stale: bool


class MediaItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    integration_id: int
    source_type: SourceType
    external_item_id: str
    external_series_id: str | None
    media_type: MediaType
    title: str
    original_title: str | None
    series_title: str | None
    year: int | None
    season_number: int | None
    episode_number: int | None
    absolute_episode_number: int | None
    monitored: bool
    file_presence: bool
    upstream_status: str | None
    poster_url: str | None
    stale: bool
    media_file: MediaFileSummary | None
    source_web_url: str | None = None


class MediaItemPage(BaseModel):
    items: list[MediaItemRead]
    page: int
    page_size: int
    total: int


class SeriesSummary(BaseModel):
    external_series_id: str
    title: str
    integration_id: int
    monitored: bool
    episode_count: int
    files_scanned: int
    episodes_missing_czech_audio: int
    errors: int
    poster_url: str | None = None
    stale: bool = False
    source_web_url: str | None = None


class SeasonSummary(BaseModel):
    integration_id: int
    external_series_id: str
    season_number: int | None
    episode_count: int
    files_scanned: int
    episodes_missing_czech_audio: int
    errors: int
    stale: bool = False


class AudioStreamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    media_file_id: int
    stream_index: int
    codec_name: str | None
    codec_long_name: str | None
    channels: int | None
    channel_layout: str | None
    sample_rate: int | None
    bit_rate: int | None
    original_language: str | None
    normalized_language: str | None
    original_title: str | None
    normalized_title: str | None
    czech_match: bool
    match_reason: str
    matched_value: str | None


class FfmpegRepairPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audio_stream_id: int = Field(ge=1)
    language_code: str = Field(default="cze", min_length=2, max_length=8)
    title: str = Field(default="Čeština", min_length=1, max_length=120)

    @field_validator("language_code")
    @classmethod
    def validate_language_code(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("Language code is required.")
        if not normalized.isalnum():
            raise ValueError("Language code must contain only letters and numbers.")
        return normalized

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Title is required.")
        return stripped


class FfmpegRepairPlan(BaseModel):
    media_file_id: int
    audio_stream_id: int
    audio_stream_index: int
    audio_stream_ordinal: int
    input_path: str
    output_path: str
    command: list[str]
    display_command: str
    warning: str
