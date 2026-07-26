"""Make all DateTime columns timezone-aware

Revision ID: 017
Revises: 016
Create Date: 2026-07-26 00:00:00.000000

Existing naive TIMESTAMP columns are converted to TIMESTAMPTZ, treating the
stored values as UTC (they were always populated via datetime.utcnow()).
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None

# (table_name, column_name)
NAIVE_DATETIME_COLUMNS = [
    ("chapter", "publish_at"),
    ("chapter", "readable_at"),
    ("chapter_metadata", "last_read_at"),
    ("external_integrations", "token_expires_at"),
    ("external_integrations", "last_sync_at"),
    ("external_manga_mappings", "last_synced_at"),
    ("manga_metadata", "last_organized_at"),
    ("manga_metadata", "last_read_at"),
    ("organization_history", "started_at"),
    ("organization_history", "completed_at"),
    ("organization_jobs", "started_at"),
    ("organization_jobs", "completed_at"),
    ("organization_jobs", "estimated_completion"),
    ("progress_operations", "started_at"),
    ("progress_operations", "completed_at"),
    ("progress_operations", "estimated_completion"),
    ("progress_operations", "last_update"),
    ("progress_events", "timestamp"),
    ("progress_events", "estimated_completion"),
    ("progress_sessions", "created_at"),
    ("progress_sessions", "last_activity"),
]


def upgrade() -> None:
    for table, column in NAIVE_DATETIME_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(timezone=False),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    for table, column in NAIVE_DATETIME_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=False),
            existing_type=sa.DateTime(timezone=True),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
