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
    
    # Add external_id field for tracking provider chapter IDs
    op.add_column('chapter', sa.Column('external_id', sa.String(255), nullable=True))
    
    # Create index on download_status for better query performance
    op.create_index('ix_chapter_download_status', 'chapter', ['download_status'])
    
    # Create index on external_id for provider lookups
    op.create_index('ix_chapter_external_id', 'chapter', ['external_id'])


def downgrade() -> None:
    """Remove download status and error fields from chapter table."""
    op.drop_index('ix_chapter_external_id', 'chapter')
    op.drop_index('ix_chapter_download_status', 'chapter')
    op.drop_column('chapter', 'external_id')
    op.drop_column('chapter', 'download_error')
    op.drop_column('chapter', 'download_status')
