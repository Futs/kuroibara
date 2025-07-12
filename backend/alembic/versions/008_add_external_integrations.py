"""Add external integrations tables

Revision ID: 008
Revises: 007
Create Date: 2024-12-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add external integrations tables."""
    
    # Create enum types
    integration_type_enum = postgresql.ENUM(
        'anilist', 'myanimelist', 
        name='integrationtype', 
        create_type=False
    )
    integration_type_enum.create(op.get_bind(), checkfirst=True)
    
    sync_status_enum = postgresql.ENUM(
        'pending', 'in_progress', 'success', 'failed', 'disabled',
        name='syncstatus',
        create_type=False
    )
    sync_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create external_integrations table
    op.create_table(
        'external_integrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('integration_type', integration_type_enum, nullable=False),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('external_user_id', sa.String(length=100), nullable=True),
        sa.Column('external_username', sa.String(length=100), nullable=True),
        sa.Column('sync_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('sync_reading_progress', sa.Boolean(), nullable=False, default=True),
        sa.Column('sync_ratings', sa.Boolean(), nullable=False, default=True),
        sa.Column('sync_status', sa.Boolean(), nullable=False, default=True),
        sa.Column('auto_sync', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_sync_status', sync_status_enum, nullable=False, default='pending'),
        sa.Column('last_sync_error', sa.Text(), nullable=True),
        sa.Column('sync_count', sa.Integer(), nullable=False, default=0),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'integration_type', name='uq_user_integration_type')
    )
    
    # Create indexes
    op.create_index('ix_external_integrations_user_id', 'external_integrations', ['user_id'])
    op.create_index('ix_external_integrations_integration_type', 'external_integrations', ['integration_type'])
    op.create_index('ix_external_integrations_last_sync_status', 'external_integrations', ['last_sync_status'])
    
    # Create external_manga_mappings table
    op.create_table(
        'external_manga_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('integration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('manga_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('external_manga_id', sa.String(length=100), nullable=False),
        sa.Column('external_title', sa.String(length=500), nullable=True),
        sa.Column('external_url', sa.String(length=500), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('sync_status', sync_status_enum, nullable=False, default='pending'),
        sa.Column('sync_error', sa.Text(), nullable=True),
        sa.Column('external_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['integration_id'], ['external_integrations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['manga_id'], ['manga.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('integration_id', 'manga_id', name='uq_integration_manga'),
        sa.UniqueConstraint('integration_id', 'external_manga_id', name='uq_integration_external_manga')
    )
    
    # Create indexes
    op.create_index('ix_external_manga_mappings_integration_id', 'external_manga_mappings', ['integration_id'])
    op.create_index('ix_external_manga_mappings_manga_id', 'external_manga_mappings', ['manga_id'])
    op.create_index('ix_external_manga_mappings_external_manga_id', 'external_manga_mappings', ['external_manga_id'])
    op.create_index('ix_external_manga_mappings_sync_status', 'external_manga_mappings', ['sync_status'])


def downgrade() -> None:
    """Remove external integrations tables."""
    
    # Drop tables
    op.drop_table('external_manga_mappings')
    op.drop_table('external_integrations')
    
    # Drop enum types
    sync_status_enum = postgresql.ENUM(name='syncstatus')
    sync_status_enum.drop(op.get_bind(), checkfirst=True)
    
    integration_type_enum = postgresql.ENUM(name='integrationtype')
    integration_type_enum.drop(op.get_bind(), checkfirst=True)
