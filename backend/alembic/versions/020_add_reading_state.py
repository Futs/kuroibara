"""Per-user reading state, activity and the chapter cache for source series (additive)

Revision ID: 020
Revises: 019
Create Date: 2026-10-17 00:00:00.000000

series_chapters      chapters cached per series from the source (shared by all users)
reading_state        per user per chapter: read, bookmark, last page (one row per user and chapter)
reading_events       append-only read/unread log per user
user_day_activity    net chapters read per user per UTC day (rollup of reading_events)
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None

_UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "series_chapters",
        sa.Column("id", _UUID, primary_key=True),
        sa.Column("series_id", _UUID, sa.ForeignKey("series.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False, server_default=""),
        sa.Column("chapter_number", sa.Float(), nullable=True),
        sa.Column("date_upload", sa.BigInteger(), nullable=True),
        sa.Column("scanlator", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("series_id", "url", name="uq_series_chapter_url"),
    )
    op.create_index("ix_series_chapters_series_id", "series_chapters", ["series_id"])

    op.create_table(
        "reading_state",
        sa.Column("user_id", _UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("chapter_id", _UUID, sa.ForeignKey("series_chapters.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("series_id", _UUID, sa.ForeignKey("series.id", ondelete="CASCADE"), nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("bookmark", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_page", sa.Integer(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reading_state_series_id", "reading_state", ["series_id"])
    op.create_index("ix_reading_state_user_series", "reading_state", ["user_id", "series_id"])

    op.create_table(
        "reading_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", _UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("series_id", _UUID, sa.ForeignKey("series.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chapter_id", _UUID, sa.ForeignKey("series_chapters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reading_events_user_at", "reading_events", ["user_id", "at"])

    op.create_table(
        "user_day_activity",
        sa.Column("user_id", _UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("day", sa.Date(), primary_key=True),
        sa.Column("chapters_read", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("user_day_activity")
    op.drop_index("ix_reading_events_user_at", table_name="reading_events")
    op.drop_table("reading_events")
    op.drop_index("ix_reading_state_user_series", table_name="reading_state")
    op.drop_index("ix_reading_state_series_id", table_name="reading_state")
    op.drop_table("reading_state")
    op.drop_index("ix_series_chapters_series_id", table_name="series_chapters")
    op.drop_table("series_chapters")
