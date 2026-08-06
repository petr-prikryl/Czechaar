from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.media import router as media_router
from app.api.v1.path_mappings import router as path_mappings_router
from app.api.v1.scans import router as scans_router
from app.api.v1.sync import router as sync_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router, tags=["system"])
api_router.include_router(integrations_router)
api_router.include_router(media_router)
api_router.include_router(path_mappings_router)
api_router.include_router(scans_router)
api_router.include_router(sync_router)
