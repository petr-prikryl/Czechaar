"""Add scan engine tables.

Revision ID: 0005_scan_engine
Revises: 0004_path_mapping_ffprobe
Create Date: 2026-08-06
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0005_scan_engine"
down_revision = "0004_path_mapping_ffprobe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scan_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scan_type", sa.String(length=40), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=True),
        sa.Column("integration_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="queued"),
        sa.Column("requested_item_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_item_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("missing_czech_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cache_hit_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cancellation_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("current_status", sa.String(length=300), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scan_runs_integration_id", "scan_runs", ["integration_id"])
    op.create_index("ix_scan_runs_scan_type", "scan_runs", ["scan_type"])
    op.create_index("ix_scan_runs_source_type", "scan_runs", ["source_type"])
    op.create_index("ix_scan_runs_status", "scan_runs", ["status"])

    op.create_table(
        "scan_run_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scan_run_id", sa.Integer(), nullable=False),
        sa.Column("media_file_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False, server_default="queued"),
        sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["media_file_id"], ["media_files.id"]),
        sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scan_run_items_media_file_id", "scan_run_items", ["media_file_id"])
    op.create_index("ix_scan_run_items_scan_run_id", "scan_run_items", ["scan_run_id"])

    op.create_table(
        "ignored_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("object_type", sa.String(length=40), nullable=False),
        sa.Column("object_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_type", "object_id", name="uq_ignored_items_object"),
    )


def downgrade() -> None:
    op.drop_table("ignored_items")
    op.drop_index("ix_scan_run_items_scan_run_id", table_name="scan_run_items")
    op.drop_index("ix_scan_run_items_media_file_id", table_name="scan_run_items")
    op.drop_table("scan_run_items")
    op.drop_index("ix_scan_runs_status", table_name="scan_runs")
    op.drop_index("ix_scan_runs_source_type", table_name="scan_runs")
    op.drop_index("ix_scan_runs_scan_type", table_name="scan_runs")
    op.drop_index("ix_scan_runs_integration_id", table_name="scan_runs")
    op.drop_table("scan_runs")
