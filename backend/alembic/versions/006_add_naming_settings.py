"""Add naming and organization settings

Revision ID: 006
Revises: 005
Create Date: 2025-07-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Check if users table exists and add columns only if they don't exist
    from alembic import context
    conn = context.get_bind()
    inspector = sa.inspect(conn)

    if 'users' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('users')]

        # Add naming and organization settings columns to users table only if they don't exist
        if 'naming_format_manga' not in existing_columns:
            op.add_column('users', sa.Column(
                'naming_format_manga',
                sa.String(500),
                nullable=False,
                server_default='{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}'
            ))

        if 'naming_format_chapter' not in existing_columns:
            op.add_column('users', sa.Column(
                'naming_format_chapter',
                sa.String(500),
                nullable=False,
                server_default='{Chapter Number} - {Chapter Name}'
            ))

        if 'auto_organize_imports' not in existing_columns:
            op.add_column('users', sa.Column(
                'auto_organize_imports',
                sa.Boolean(),
                nullable=False,
                server_default='true'
            ))

        if 'create_cbz_files' not in existing_columns:
            op.add_column('users', sa.Column(
                'create_cbz_files',
                sa.Boolean(),
                nullable=False,
                server_default='true'
            ))

        if 'preserve_original_files' not in existing_columns:
            op.add_column('users', sa.Column(
                'preserve_original_files',
                sa.Boolean(),
                nullable=False,
                server_default='false'
            ))


def downgrade():
    # Check if users table exists and remove columns only if they exist
    from alembic import context
    conn = context.get_bind()
    inspector = sa.inspect(conn)

    if 'users' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('users')]

        # Remove naming and organization settings columns from users table only if they exist
        if 'preserve_original_files' in existing_columns:
            op.drop_column('users', 'preserve_original_files')

        if 'create_cbz_files' in existing_columns:
            op.drop_column('users', 'create_cbz_files')

        if 'auto_organize_imports' in existing_columns:
            op.drop_column('users', 'auto_organize_imports')

        if 'naming_format_chapter' in existing_columns:
            op.drop_column('users', 'naming_format_chapter')

        if 'naming_format_manga' in existing_columns:
            op.drop_column('users', 'naming_format_manga')
