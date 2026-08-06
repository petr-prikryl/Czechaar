from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.ignored import IgnoredItem
from app.schemas.ignored import IgnoredItemCreate, IgnoredItemRead

router = APIRouter(prefix="/ignored", tags=["ignored"])


@router.get("", response_model=list[IgnoredItemRead])
def list_ignored_items(session: Session = Depends(get_session)) -> list[IgnoredItem]:
    return list(session.scalars(select(IgnoredItem).order_by(IgnoredItem.created_at.desc())))


@router.post("", response_model=IgnoredItemRead, status_code=status.HTTP_201_CREATED)
def ignore_item(payload: IgnoredItemCreate, session: Session = Depends(get_session)) -> IgnoredItem:
    existing = session.scalar(
        select(IgnoredItem).where(
            IgnoredItem.object_type == payload.object_type,
            IgnoredItem.object_id == payload.object_id,
        )
    )
    if existing is not None:
        return existing
    item = IgnoredItem(
        object_type=payload.object_type,
        object_id=payload.object_id,
        reason=payload.reason,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{ignored_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def unignore_item(ignored_item_id: int, session: Session = Depends(get_session)) -> None:
    item = session.get(IgnoredItem, ignored_item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ignored item not found.")
    session.delete(item)
    session.commit()
