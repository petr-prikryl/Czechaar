"""Add media synchronization tables.

Revision ID: 0003_library_sync
Revises: 0002_integrations
Create Date: 2026-08-06
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003_library_sync"
down_revision = "0002_integrations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "media_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("external_item_id", sa.String(length=80), nullable=False),
        sa.Column("external_series_id", sa.String(length=80), nullable=True),
        sa.Column("media_type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("original_title", sa.String(length=500), nullable=True),
        sa.Column("series_title", sa.String(length=500), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("season_number", sa.Integer(), nullable=True),
        sa.Column("episode_number", sa.Integer(), nullable=True),
        sa.Column("absolute_episode_number", sa.Integer(), nullable=True),
        sa.Column("monitored", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("file_presence", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("upstream_status", sa.String(length=120), nullable=True),
        sa.Column("poster_url", sa.Text(), nullable=True),
        sa.Column("stale", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "integration_id",
            "media_type",
            "external_item_id",
            name="uq_media_items_integration_media_external",
        ),
    )
    op.create_index("ix_media_items_external_series_id", "media_items", ["external_series_id"])
    op.create_index("ix_media_items_integration_id", "media_items", ["integration_id"])
    op.create_index("ix_media_items_media_type", "media_items", ["media_type"])
    op.create_index("ix_media_items_source_type", "media_items", ["source_type"])
    op.create_index("ix_media_items_stale", "media_items", ["stale"])

    op.create_table(
        "media_files",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("external_file_id", sa.String(length=80), nullable=False),
        sa.Column("original_source_path", sa.Text(), nullable=False),
        sa.Column("mapped_local_path", sa.Text(), nullable=True),
        sa.Column("relative_path", sa.Text(), nullable=True),
        sa.Column("size", sa.Integer(), nullable=True),
        sa.Column("modified_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quality", sa.String(length=200), nullable=True),
        sa.Column("quality_profile", sa.String(length=200), nullable=True),
        sa.Column("fingerprint", sa.String(length=200), nullable=True),
        sa.Column("scan_state", sa.String(length=80), nullable=False, server_default="not_scanned"),
        sa.Column("czech_audio_result", sa.Boolean(), nullable=True),
        sa.Column("analyzer_version", sa.String(length=80), nullable=True),
        sa.Column("last_successful_scan", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_scan_attempt", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("sanitized_error_message", sa.Text(), nullable=True),
        sa.Column("stale", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("integration_id", "external_file_id", name="uq_media_files_integration_external"),
    )
    op.create_index("ix_media_files_integration_id", "media_files", ["integration_id"])
    op.create_index("ix_media_files_scan_state", "media_files", ["scan_state"])
    op.create_index("ix_media_files_source_type", "media_files", ["source_type"])
    op.create_index("ix_media_files_stale", "media_files", ["stale"])

    op.create_table(
        "media_item_file_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("media_item_id", sa.Integer(), nullable=False),
        sa.Column("media_file_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["media_file_id"], ["media_files.id"]),
        sa.ForeignKeyConstraint(["media_item_id"], ["media_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("media_item_id", "media_file_id", name="uq_media_item_file_links_item_file"),
    )
    op.create_index("ix_media_item_file_links_media_file_id", "media_item_file_links", ["media_file_id"])
    op.create_index("ix_media_item_file_links_media_item_id", "media_item_file_links", ["media_item_id"])

    op.create_table(
        "library_sync_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=True),
        sa.Column("integration_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("items_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("files_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stale_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_library_sync_runs_integration_id", "library_sync_runs", ["integration_id"])
    op.create_index("ix_library_sync_runs_source_type", "library_sync_runs", ["source_type"])


def downgrade() -> None:
    op.drop_index("ix_library_sync_runs_source_type", table_name="library_sync_runs")
    op.drop_index("ix_library_sync_runs_integration_id", table_name="library_sync_runs")
    op.drop_table("library_sync_runs")
    op.drop_index("ix_media_item_file_links_media_item_id", table_name="media_item_file_links")
    op.drop_index("ix_media_item_file_links_media_file_id", table_name="media_item_file_links")
    op.drop_table("media_item_file_links")
    op.drop_index("ix_media_files_stale", table_name="media_files")
    op.drop_index("ix_media_files_source_type", table_name="media_files")
    op.drop_index("ix_media_files_scan_state", table_name="media_files")
    op.drop_index("ix_media_files_integration_id", table_name="media_files")
    op.drop_table("media_files")
    op.drop_index("ix_media_items_stale", table_name="media_items")
    op.drop_index("ix_media_items_source_type", table_name="media_items")
    op.drop_index("ix_media_items_media_type", table_name="media_items")
    op.drop_index("ix_media_items_integration_id", table_name="media_items")
    op.drop_index("ix_media_items_external_series_id", table_name="media_items")
    op.drop_table("media_items")
