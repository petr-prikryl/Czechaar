from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SourceType


class PathMappingBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    integration_id: int | None = Field(default=None, ge=1)
    source_type: SourceType | None = None
    remote_path_prefix: str = Field(min_length=1, max_length=1000)
    local_path_prefix: str = Field(min_length=1, max_length=1000)
    enabled: bool = True
    priority: int = 100
    description: str | None = Field(default=None, max_length=500)


class PathMappingCreate(PathMappingBase):
    pass


class PathMappingRead(PathMappingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PathMappingTestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    remote_path: str
    source_type: SourceType
    integration_id: int = Field(ge=1)


class PathMappingTestResponse(BaseModel):
    original_path: str
    mapped_path: str | None
    mapping_id: int | None
    status: str
    inside_allowed_root: bool | None = None


class AllowedMediaRootCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1, max_length=1000)
    enabled: bool = True
    description: str | None = Field(default=None, max_length=500)


class AllowedMediaRootRead(AllowedMediaRootCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exists: bool
    readable: bool
    created_at: datetime
    updated_at: datetime
