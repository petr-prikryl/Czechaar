"""Add external web URLs and listing indexes.

Revision ID: 0006_web_urls_and_listing_indexes
Revises: 0005_scan_engine
Create Date: 2026-08-06
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0006_web_urls_and_listing_indexes"
down_revision = "0005_scan_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("integrations", sa.Column("web_url", sa.String(length=500), nullable=True))
    op.add_column(
        "media_items",
        sa.Column("external_web_path", sa.String(length=500), nullable=True),
    )
    op.create_index(
        "ix_media_items_series_season",
        "media_items",
        ["integration_id", "external_series_id", "season_number"],
    )
    op.create_index(
        "ix_media_files_missing_listing",
        "media_files",
        ["scan_state", "stale", "integration_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_media_files_missing_listing", table_name="media_files")
    op.drop_index("ix_media_items_series_season", table_name="media_items")
    op.drop_column("media_items", "external_web_path")
    op.drop_column("integrations", "web_url")
