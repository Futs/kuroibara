"""Persisted download queue for extension-source chapters (Mihon-style; additive)

Revision ID: 019
Revises: 018
Create Date: 2026-10-17 00:00:00.000000

source_downloads: one row per chapter queued from an extension source. Status moves
queued -> downloading -> downloaded | error. Page list is stored once. Survives restarts.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_downloads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("series_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("series.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module", sa.String(length=120), nullable=False),
        sa.Column("chapter_url", sa.Text(), nullable=False),
        sa.Column("chapter_name", sa.String(length=500), nullable=False),
        sa.Column("chapter_number", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
        sa.Column("pages", postgresql.JSONB(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("path", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("claimed_by", sa.String(length=120), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("series_id", "module", "chapter_url", name="uq_source_download_chapter"),
    )
    op.create_index("ix_source_downloads_series_id", "source_downloads", ["series_id"])
    op.create_index("ix_source_downloads_status", "source_downloads", ["status"])


def downgrade() -> None:
    op.drop_index("ix_source_downloads_status", table_name="source_downloads")
    op.drop_index("ix_source_downloads_series_id", table_name="source_downloads")
    op.drop_table("source_downloads")
