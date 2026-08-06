from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings
from app.schemas.health import HealthResponse, ReadinessResponse, VersionResponse
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
        git_commit=settings.git_commit,
        build_date=settings.build_date,
    )
