"""Add download status and error fields to chapter table

Revision ID: 014
Revises: 013
Create Date: 2025-08-11 18:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add download status and error fields to chapter table."""
    # Add download_status field with default value
    op.add_column('chapter', sa.Column('download_status', sa.String(20), nullable=False, server_default='not_downloaded'))

    # Add download_error field for storing error messages
    op.add_column('chapter', sa.Column('download_error', sa.Text(), nullable=True))

    # Note: external_id already exists from base migration 000_create_base_tables.py
    # No need to add it again

    # Create index on download_status for better query performance
    op.create_index('ix_chapter_download_status', 'chapter', ['download_status'])

    # Note: ix_chapter_external_id index already exists from base migration


def downgrade() -> None:
    """Remove download status and error fields from chapter table."""
    # Only drop the index and columns we added in this migration
    op.drop_index('ix_chapter_download_status', 'chapter')
    op.drop_column('chapter', 'download_error')
    op.drop_column('chapter', 'download_status')

    # Note: Don't drop external_id or its index as they existed before this migration
