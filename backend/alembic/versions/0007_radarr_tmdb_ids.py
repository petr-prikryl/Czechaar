"""Store Radarr TMDb identifiers separately.

Revision ID: 0007_radarr_tmdb_ids
Revises: 0006_web_urls_and_listing_indexes
Create Date: 2026-08-18
"""

from __future__ import annotations

import re

import sqlalchemy as sa

from alembic import op

revision = "0007_radarr_tmdb_ids"
down_revision = "0006_web_urls_and_listing_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("media_items", sa.Column("external_tmdb_id", sa.String(length=80), nullable=True))
    _backfill_tmdb_ids_from_web_paths()


def downgrade() -> None:
    op.drop_column("media_items", "external_tmdb_id")


def _backfill_tmdb_ids_from_web_paths() -> None:
    media_items = sa.table(
        "media_items",
        sa.column("id", sa.Integer()),
        sa.column("source_type", sa.String(length=20)),
        sa.column("media_type", sa.String(length=20)),
        sa.column("external_item_id", sa.String(length=80)),
        sa.column("external_tmdb_id", sa.String(length=80)),
        sa.column("external_web_path", sa.String(length=500)),
    )
    connection = op.get_bind()
    rows = connection.execute(
        sa.select(
            media_items.c.id,
            media_items.c.external_item_id,
            media_items.c.external_web_path,
        )
        .where(media_items.c.source_type == "radarr")
        .where(media_items.c.media_type == "movie")
        .where(media_items.c.external_tmdb_id.is_(None))
        .where(media_items.c.external_web_path.is_not(None))
    ).mappings()

    for row in rows:
        match = re.fullmatch(r"/?movie/(\d+)/?", str(row["external_web_path"]).strip())
        if not match:
            continue
        tmdb_id = match.group(1)
        if tmdb_id == str(row["external_item_id"]):
            continue
        connection.execute(
            media_items.update()
            .where(media_items.c.id == row["id"])
            .values(external_tmdb_id=tmdb_id)
        )
