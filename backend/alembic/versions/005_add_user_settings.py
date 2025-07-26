"""Add user settings fields

Revision ID: 005
Revises: 004
Create Date: 2025-07-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Check if users table exists and add columns only if they don't exist
    from alembic import context
    conn = context.get_bind()
    inspector = sa.inspect(conn)

    if 'users' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('users')]

        # Add user settings columns to users table only if they don't exist
        if 'theme' not in existing_columns:
            op.add_column('users', sa.Column('theme', sa.String(20), nullable=False, server_default='light'))

        if 'nsfw_blur' not in existing_columns:
            op.add_column('users', sa.Column('nsfw_blur', sa.Boolean(), nullable=False, server_default='true'))

        if 'download_quality' not in existing_columns:
            op.add_column('users', sa.Column('download_quality', sa.String(20), nullable=False, server_default='high'))

        if 'download_path' not in existing_columns:
            op.add_column('users', sa.Column('download_path', sa.String(500), nullable=False, server_default='/app/storage'))


def downgrade():
    # Check if users table exists and remove columns only if they exist
    from alembic import context
    conn = context.get_bind()
    inspector = sa.inspect(conn)

    if 'users' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('users')]

        # Remove user settings columns from users table only if they exist
        if 'download_path' in existing_columns:
            op.drop_column('users', 'download_path')

        if 'download_quality' in existing_columns:
            op.drop_column('users', 'download_quality')

        if 'nsfw_blur' in existing_columns:
            op.drop_column('users', 'nsfw_blur')

        if 'theme' in existing_columns:
            op.drop_column('users', 'theme')
