"""Make all DateTime columns timezone-aware

Revision ID: 017
Revises: 016
Create Date: 2026-07-26 00:00:00.000000

Existing naive TIMESTAMP columns are converted to TIMESTAMPTZ, treating the
stored values as UTC (they were always populated via datetime.utcnow()).

progress_operations/progress_events/progress_sessions never had a creation
migration - they only ever existed via the app's Base.metadata.create_all()
dev fallback - so this also creates them (already timezone-aware) if they're
missing, and only falls back to ALTER on them if they already exist from
that fallback with naive columns.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None

# (table_name, column_name) for tables guaranteed to already exist via an
# earlier migration.
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
    # created_at/updated_at as originally written into migrations 007/008,
    # predating BaseModel's switch to timezone-aware columns.
    ("manga_metadata", "created_at"),
    ("manga_metadata", "updated_at"),
    ("chapter_metadata", "created_at"),
    ("chapter_metadata", "updated_at"),
    ("organization_history", "created_at"),
    ("organization_history", "updated_at"),
    ("organization_jobs", "created_at"),
    ("organization_jobs", "updated_at"),
    ("external_integrations", "created_at"),
    ("external_integrations", "updated_at"),
    ("external_manga_mappings", "created_at"),
    ("external_manga_mappings", "updated_at"),
]

# (table_name, column_name) for the progress_* tables, which may or may not
# exist depending on whether create_all() ever ran against this database.
PROGRESS_DATETIME_COLUMNS = [
    ("progress_operations", "started_at"),
    ("progress_operations", "completed_at"),
    ("progress_operations", "estimated_completion"),
    ("progress_operations", "last_update"),
    ("progress_events", "timestamp"),
    ("progress_events", "estimated_completion"),
    ("progress_sessions", "created_at"),
    ("progress_sessions", "last_activity"),
]


def _create_progress_tables() -> None:
    op.create_table(
        "progress_operations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("operation_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("progress_percentage", sa.Float(), server_default="0.0"),
        sa.Column("current_step", sa.String(255), nullable=True),
        sa.Column("total_steps", sa.Integer(), nullable=True),
        sa.Column("current_step_number", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_completion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_update", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("warning_messages", postgresql.JSON(), nullable=True),
        sa.Column("operation_metadata", postgresql.JSON(), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_id", sa.String(255), nullable=True),
        sa.Column(
            "parent_operation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("progress_operations.id"),
            nullable=True,
        ),
        sa.Column("total_items", sa.Integer(), nullable=True),
        sa.Column("processed_items", sa.Integer(), server_default="0"),
        sa.Column("successful_items", sa.Integer(), server_default="0"),
        sa.Column("failed_items", sa.Integer(), server_default="0"),
        sa.Column("is_cancellable", sa.Boolean(), server_default=sa.true()),
        sa.Column("cancellation_token", sa.String(255), nullable=True),
    )
    op.create_index(
        "idx_progress_operations_user_status",
        "progress_operations",
        ["user_id", "status"],
    )
    op.create_index(
        "idx_progress_operations_session_status",
        "progress_operations",
        ["session_id", "status"],
    )
    op.create_index(
        "idx_progress_operations_type_status",
        "progress_operations",
        ["operation_type", "status"],
    )
    op.create_index(
        "idx_progress_operations_started_at", "progress_operations", ["started_at"]
    )
    op.create_index(
        "idx_progress_operations_last_update", "progress_operations", ["last_update"]
    )

    op.create_table(
        "progress_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "operation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("progress_operations.id"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("progress_percentage", sa.Float(), server_default="0.0"),
        sa.Column("current_step", sa.String(255), nullable=True),
        sa.Column("total_steps", sa.Integer(), nullable=True),
        sa.Column("current_step_number", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("warning_message", sa.Text(), nullable=True),
        sa.Column("event_metadata", postgresql.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estimated_completion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_id", sa.String(255), nullable=True),
    )
    op.create_index(
        "idx_progress_events_operation_timestamp",
        "progress_events",
        ["operation_id", "timestamp"],
    )
    op.create_index(
        "idx_progress_events_user_timestamp",
        "progress_events",
        ["user_id", "timestamp"],
    )
    op.create_index(
        "idx_progress_events_session_timestamp",
        "progress_events",
        ["session_id", "timestamp"],
    )
    op.create_index(
        "idx_progress_events_type_timestamp",
        "progress_events",
        ["event_type", "timestamp"],
    )

    op.create_table(
        "progress_sessions",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("client_info", postgresql.JSON(), nullable=True),
        sa.Column("session_metadata", postgresql.JSON(), nullable=True),
    )
    op.create_index(
        "idx_progress_sessions_user_active",
        "progress_sessions",
        ["user_id", "is_active"],
    )
    op.create_index(
        "idx_progress_sessions_last_activity", "progress_sessions", ["last_activity"]
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "progress_operations" not in existing_tables:
        # Fresh database (e.g. CI) - create the tables timezone-aware from
        # the start, nothing to alter afterwards.
        _create_progress_tables()
    else:
        # Already exists via create_all() - bring its columns up to
        # timezone-aware like everything else below.
        for table, column in PROGRESS_DATETIME_COLUMNS:
            op.alter_column(
                table,
                column,
                type_=sa.DateTime(timezone=True),
                existing_type=sa.DateTime(timezone=False),
                postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            )

    for table, column in NAIVE_DATETIME_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(timezone=False),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    for table, column in NAIVE_DATETIME_COLUMNS + PROGRESS_DATETIME_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=False),
            existing_type=sa.DateTime(timezone=True),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
