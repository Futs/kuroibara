"""User time zones; local day on reading events (additive, with backfill)

Revision ID: 021
Revises: 020
Create Date: 2026-10-17 00:00:00.000000

users.timezone          IANA name, null = use the server's TZ
reading_events.local_day  calendar day in the user's zone when the event was written
Existing events are backfilled with their UTC day, which is what they were counted under before.
"""

import sqlalchemy as sa

from alembic import op

revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("timezone", sa.String(length=64), nullable=True))
    op.add_column("reading_events", sa.Column("local_day", sa.Date(), nullable=True))
    op.execute("UPDATE reading_events SET local_day = (at AT TIME ZONE 'UTC')::date WHERE local_day IS NULL")
    op.alter_column("reading_events", "local_day", nullable=False)


def downgrade() -> None:
    op.drop_column("reading_events", "local_day")
    op.drop_column("users", "timezone")
