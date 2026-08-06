from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.scan import ScanRun, ScanRunItem
from app.schemas.scan import ScanProgressResponse, ScanRunRead, ScanStartRequest
from app.services.scan_engine import ScanEngine, scan_runner

router = APIRouter(prefix="/scans", tags=["scans"])
background_scan_tasks: set[asyncio.Task[None]] = set()


@router.post("", response_model=ScanRunRead, status_code=status.HTTP_202_ACCEPTED)
async def start_scan(
    payload: ScanStartRequest,
    session: Session = Depends(get_session),
) -> ScanRun:
    run, file_ids, force = ScanEngine(session).create_scan(payload, force=payload.force)
    task = asyncio.create_task(scan_runner.run(run.id, file_ids, force=force))
    background_scan_tasks.add(task)
    task.add_done_callback(background_scan_tasks.discard)
    return run


@router.get("/history", response_model=list[ScanRunRead])
def list_scan_history(session: Session = Depends(get_session)) -> list[ScanRun]:
    statement = select(ScanRun).order_by(ScanRun.created_at.desc()).limit(100)
    return list(session.scalars(statement))


@router.get("/{scan_run_id}", response_model=ScanRunRead)
def get_scan(scan_run_id: int, session: Session = Depends(get_session)) -> ScanRun:
    run = session.get(ScanRun, scan_run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan run not found.")
    return run


@router.get("/{scan_run_id}/progress", response_model=ScanProgressResponse)
def get_scan_progress(
    scan_run_id: int,
    session: Session = Depends(get_session),
) -> ScanProgressResponse:
    run = session.get(ScanRun, scan_run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan run not found.")
    items = list(
        session.scalars(
            select(ScanRunItem)
            .where(ScanRunItem.scan_run_id == scan_run_id)
            .order_by(ScanRunItem.id)
        )
    )
    return ScanProgressResponse(run=ScanRunRead.model_validate(run), items=items)


@router.post("/{scan_run_id}/cancel", response_model=ScanRunRead)
def cancel_scan(scan_run_id: int, session: Session = Depends(get_session)) -> ScanRun:
    if not scan_runner.cancel(scan_run_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan run not found.")
    run = session.get(ScanRun, scan_run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan run not found.")
    session.refresh(run)
    return run
