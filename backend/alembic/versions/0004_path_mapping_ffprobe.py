"""Add path mappings, media roots and audio streams.

Revision ID: 0004_path_mapping_ffprobe
Revises: 0003_library_sync
Create Date: 2026-08-06
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004_path_mapping_ffprobe"
down_revision = "0003_library_sync"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "path_mappings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=True),
        sa.Column("source_type", sa.String(length=20), nullable=True),
        sa.Column("remote_path_prefix", sa.Text(), nullable=False),
        sa.Column("local_path_prefix", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_path_mappings_integration_id", "path_mappings", ["integration_id"])
    op.create_index("ix_path_mappings_source_type", "path_mappings", ["source_type"])

    op.create_table(
        "allowed_media_roots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("path"),
    )

    op.create_table(
        "audio_streams",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("media_file_id", sa.Integer(), nullable=False),
        sa.Column("stream_index", sa.Integer(), nullable=False),
        sa.Column("codec_name", sa.String(length=120), nullable=True),
        sa.Column("codec_long_name", sa.String(length=300), nullable=True),
        sa.Column("channels", sa.Integer(), nullable=True),
        sa.Column("channel_layout", sa.String(length=120), nullable=True),
        sa.Column("sample_rate", sa.Integer(), nullable=True),
        sa.Column("bit_rate", sa.Integer(), nullable=True),
        sa.Column("original_language", sa.String(length=120), nullable=True),
        sa.Column("normalized_language", sa.String(length=120), nullable=True),
        sa.Column("original_title", sa.Text(), nullable=True),
        sa.Column("normalized_title", sa.Text(), nullable=True),
        sa.Column("czech_match", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("match_reason", sa.String(length=80), nullable=False, server_default="no_match"),
        sa.Column("matched_value", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["media_file_id"], ["media_files.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("media_file_id", "stream_index", name="uq_audio_streams_file_stream_index"),
    )
    op.create_index("ix_audio_streams_media_file_id", "audio_streams", ["media_file_id"])


def downgrade() -> None:
    op.drop_index("ix_audio_streams_media_file_id", table_name="audio_streams")
    op.drop_table("audio_streams")
    op.drop_table("allowed_media_roots")
    op.drop_index("ix_path_mappings_source_type", table_name="path_mappings")
    op.drop_index("ix_path_mappings_integration_id", table_name="path_mappings")
    op.drop_table("path_mappings")
