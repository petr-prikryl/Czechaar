from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.sync import LibrarySyncRun
from app.schemas.sync import LibrarySyncRequest, LibrarySyncRunRead
from app.services.library_sync import LibrarySyncService

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/library", response_model=LibrarySyncRunRead)
async def synchronize_library(
    payload: LibrarySyncRequest,
    session: Session = Depends(get_session),
) -> LibrarySyncRun:
    return await LibrarySyncService(session).synchronize(
        source_type=payload.source_type,
        integration_id=payload.integration_id,
    )


@router.get("/history", response_model=list[LibrarySyncRunRead])
def list_sync_history(session: Session = Depends(get_session)) -> list[LibrarySyncRun]:
    statement = select(LibrarySyncRun).order_by(LibrarySyncRun.started_at.desc()).limit(100)
    return list(session.scalars(statement))
