"""Groups (admin, user), user membership, and app settings for first-run setup

Revision ID: 022
Revises: 021
Create Date: 2026-10-17 00:00:00.000000

groups        admin and user (fixed ids 1 and 2)
user_groups   membership. Every existing user joins `user`; existing superusers also join `admin`.
app_settings  key/value. An existing install (users already present) is marked set up, so it does not
              start the first-run wizard.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "user_groups",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.execute("INSERT INTO groups (id, name, description) VALUES "
               "(1, 'admin', 'Full access, including server and user management'), "
               "(2, 'user', 'Use the library and change own settings')")
    op.execute("INSERT INTO user_groups (user_id, group_id) SELECT id, 2 FROM users")
    op.execute("INSERT INTO user_groups (user_id, group_id) SELECT id, 1 FROM users WHERE is_superuser")
    op.execute("INSERT INTO app_settings (key, value) "
               "SELECT 'setup_completed', '{\"legacy\": true}'::jsonb WHERE EXISTS (SELECT 1 FROM users)")


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_table("user_groups")
    op.drop_table("groups")
