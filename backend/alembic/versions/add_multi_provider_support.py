"""Add multi-provider support to chapters

Revision ID: add_multi_provider_support
Revises: 
Create Date: 2025-08-22 18:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_multi_provider_support'
down_revision = None  # Will be updated to latest revision
branch_labels = None
depends_on = None


def upgrade():
    """Add multi-provider support fields to chapter table."""
    # Add provider_external_ids JSONB column
    op.add_column('chapter', sa.Column('provider_external_ids', postgresql.JSONB(), nullable=True))
    
    # Add fallback_providers JSONB column  
    op.add_column('chapter', sa.Column('fallback_providers', postgresql.JSONB(), nullable=True))
    
    # Create index on provider_external_ids for faster lookups
    op.create_index('ix_chapter_provider_external_ids', 'chapter', ['provider_external_ids'], postgresql_using='gin')


def downgrade():
    """Remove multi-provider support fields from chapter table."""
    # Drop index
    op.drop_index('ix_chapter_provider_external_ids', table_name='chapter')
    
    # Drop columns
    op.drop_column('chapter', 'fallback_providers')
    op.drop_column('chapter', 'provider_external_ids')
