from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db.session import initialize_database
from app.services.scan_engine import recover_interrupted_scans
from app.workers.scheduler import ScheduledScanWorker


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings)
    initialize_database()
    recover_interrupted_scans()
    scheduler = ScheduledScanWorker(settings)
    scheduler.start()
    yield
    await scheduler.stop()


def _frontend_dist(settings: Settings) -> Path | None:
    candidates: list[Path] = []
    if settings.static_dir is not None:
        candidates.append(settings.static_dir)
    candidates.append(Path(__file__).resolve().parents[2] / "frontend" / "dist")

    for candidate in candidates:
        index_path = candidate / "index.html"
        if index_path.is_file():
            return candidate
    return None


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Czecharr API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    frontend_dist = _frontend_dist(settings)
    if frontend_dist is not None:
        assets_dir = frontend_dist / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

        @app.get("/", include_in_schema=False)
        def frontend_root() -> FileResponse:
            return FileResponse(frontend_dist / "index.html")

        @app.get("/{full_path:path}", include_in_schema=False)
        def frontend_fallback(full_path: str) -> FileResponse:
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail="Not found")
            return FileResponse(frontend_dist / "index.html")

        return app

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {"application": settings.app_name}

    return app


app = create_app()
