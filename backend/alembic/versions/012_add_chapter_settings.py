"""Add chapter and storage settings to user table

Revision ID: 012
Revises: 011
Create Date: 2025-07-18 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if columns already exist before adding them
    from alembic import context
    conn = context.get_bind()
    inspector = sa.inspect(conn)

    if 'users' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('users')]

        # Add chapter settings columns if they don't exist
        if 'chapter_auto_refresh_interval' not in existing_columns:
            op.add_column('users', sa.Column('chapter_auto_refresh_interval', sa.Integer(), nullable=False, server_default='300'))

        if 'chapter_check_on_tab_focus' not in existing_columns:
            op.add_column('users', sa.Column('chapter_check_on_tab_focus', sa.Boolean(), nullable=False, server_default='true'))

        if 'chapter_show_update_notifications' not in existing_columns:
            op.add_column('users', sa.Column('chapter_show_update_notifications', sa.Boolean(), nullable=False, server_default='true'))

        if 'chapter_enable_manual_refresh' not in existing_columns:
            op.add_column('users', sa.Column('chapter_enable_manual_refresh', sa.Boolean(), nullable=False, server_default='true'))

        # Add storage settings columns if they don't exist
        if 'storage_type' not in existing_columns:
            op.add_column('users', sa.Column('storage_type', sa.String(20), nullable=False, server_default='local'))

        if 'max_upload_size' not in existing_columns:
            op.add_column('users', sa.Column('max_upload_size', sa.String(10), nullable=False, server_default='100MB'))


def downgrade() -> None:
    # Remove the columns
    op.drop_column('users', 'max_upload_size')
    op.drop_column('users', 'storage_type')
    op.drop_column('users', 'chapter_enable_manual_refresh')
    op.drop_column('users', 'chapter_show_update_notifications')
    op.drop_column('users', 'chapter_check_on_tab_focus')
    op.drop_column('users', 'chapter_auto_refresh_interval')
