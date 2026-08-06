from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import MediaType
from app.models.media import MediaFile, MediaItem, MediaItemFileLink


class MediaRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_item(
        self,
        *,
        integration_id: int,
        media_type: MediaType,
        external_item_id: str,
    ) -> MediaItem | None:
        statement = select(MediaItem).where(
            MediaItem.integration_id == integration_id,
            MediaItem.media_type == media_type,
            MediaItem.external_item_id == external_item_id,
        )
        return self.session.scalar(statement)

    def get_file(self, *, integration_id: int, external_file_id: str) -> MediaFile | None:
        statement = select(MediaFile).where(
            MediaFile.integration_id == integration_id,
            MediaFile.external_file_id == external_file_id,
        )
        return self.session.scalar(statement)

    def ensure_link(self, media_item: MediaItem, media_file: MediaFile) -> None:
        self.session.flush()
        statement = select(MediaItemFileLink).where(
            MediaItemFileLink.media_item_id == media_item.id,
            MediaItemFileLink.media_file_id == media_file.id,
        )
        if self.session.scalar(statement) is None:
            self.session.add(MediaItemFileLink(media_item=media_item, media_file=media_file))

    def paged_items(
        self,
        statement: Select[tuple[MediaItem]],
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[MediaItem], int]:
        count_statement = select(func.count()).select_from(statement.order_by(None).subquery())
        total = self.session.scalar(count_statement) or 0
        items = list(
            self.session.scalars(
                statement.options(
                    selectinload(MediaItem.file_links).selectinload(MediaItemFileLink.media_file)
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total
