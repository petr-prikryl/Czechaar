from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings
from app.schemas.health import (
    HealthResponse,
    ReadinessResponse,
    RuntimeSettingsResponse,
    VersionResponse,
)
from app.services.readiness import get_readiness

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadinessResponse)
def ready() -> ReadinessResponse:
    return get_readiness()


@router.get("/version", response_model=VersionResponse)
def version() -> VersionResponse:
    settings = get_settings()
    return VersionResponse(
        application="Czecharr",
        version=__version__,
        api_version="v1",
        demo_mode=settings.demo_mode,
        git_commit=settings.git_commit,
        build_date=settings.build_date,
    )


@router.get("/runtime-settings", response_model=RuntimeSettingsResponse)
def runtime_settings() -> RuntimeSettingsResponse:
    settings = get_settings()
    return RuntimeSettingsResponse(
        ffprobe_path=settings.ffprobe_path,
        ffprobe_timeout=settings.ffprobe_timeout,
        scan_concurrency=settings.scan_concurrency,
        scheduled_scan_enabled=settings.scheduled_scan_enabled,
        scheduled_scan_interval_minutes=settings.scheduled_scan_interval_minutes,
        stale_retention_days=settings.stale_retention_days,
        timezone=settings.timezone,
    )
