"""Add extension-host library entries and their metadata (additive; existing tables untouched)

Revision ID: 018
Revises: 017
Create Date: 2026-10-17 00:00:00.000000

series           one library entry per title per source (Mihon's model). Migrating to another source
                 creates a second entry; the old one is kept, with in_library = false.
series_metadata  provider snapshot (base) and current values with origin per field, plus the cached
                 MangaUpdates entry (Phase 2b).

Strangler pattern (D4): the legacy manga/provider tables are not changed.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "series",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("module", sa.String(length=120), nullable=False),
        sa.Column("package", sa.String(length=255), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("source_lang", sa.String(length=20), nullable=False),
        sa.Column("source_id", sa.String(length=40), nullable=True),
        sa.Column("series_url", sa.Text(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("cover_url", sa.Text(), nullable=True),
        sa.Column("is_nsfw", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("content_warning", sa.String(length=40), nullable=True),
        sa.Column("in_library", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("module", "series_url", name="uq_series_source_url"),
    )
    op.create_index("ix_series_title", "series", ["title"])
    op.create_index("ix_series_in_library", "series", ["in_library"])

    op.create_table(
        "series_metadata",
        sa.Column("series_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("series.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("base", postgresql.JSONB(), nullable=False),
        sa.Column("current", postgresql.JSONB(), nullable=False),
        sa.Column("mangaupdates", postgresql.JSONB(), nullable=True),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("series_metadata")
    op.drop_index("ix_series_in_library", table_name="series")
    op.drop_index("ix_series_title", table_name="series")
    op.drop_table("series")
