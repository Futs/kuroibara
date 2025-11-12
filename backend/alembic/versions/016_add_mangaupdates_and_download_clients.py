"""Add MangaUpdates integration and download client support

Revision ID: 016
Revises: 015
Create Date: 2025-08-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add MangaUpdates integration and download client support."""
    
    # Create universal_manga_entries table
    op.create_table(
        'universal_manga_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),

        # Source information
        sa.Column('source_indexer', sa.String(50), nullable=False, index=True),
        sa.Column('source_id', sa.String(100), nullable=False, index=True),
        sa.Column('source_url', sa.String(500), nullable=True),
        
        # Core metadata
        sa.Column('title', sa.String(500), nullable=False, index=True),
        sa.Column('alternative_titles', postgresql.JSONB, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('cover_image_url', sa.String(500), nullable=True),
        
        # Series information
        sa.Column('type', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('year', sa.Integer, nullable=True),
        sa.Column('completed_year', sa.Integer, nullable=True),
        
        # Content ratings
        sa.Column('is_nsfw', sa.Boolean, default=False, nullable=False),
        sa.Column('content_rating', sa.String(20), nullable=True),
        sa.Column('demographic', sa.String(20), nullable=True),

        # Enhanced metadata for tiered system
        sa.Column('genres', postgresql.JSONB, nullable=True),
        sa.Column('tags', postgresql.JSONB, nullable=True),
        sa.Column('themes', postgresql.JSONB, nullable=True),
        sa.Column('categories', postgresql.JSONB, nullable=True),

        # People
        sa.Column('authors', postgresql.JSONB, nullable=True),
        sa.Column('artists', postgresql.JSONB, nullable=True),
        sa.Column('publishers', postgresql.JSONB, nullable=True),
        
        # Statistics (can come from any indexer)
        sa.Column('rating', sa.Float, nullable=True),
        sa.Column('rating_count', sa.Integer, nullable=True),
        sa.Column('popularity_rank', sa.Integer, nullable=True),
        sa.Column('follows', sa.Integer, nullable=True),

        # Chapter information
        sa.Column('latest_chapter', sa.String(20), nullable=True),
        sa.Column('total_chapters', sa.Integer, nullable=True),

        # Quality and confidence scoring
        sa.Column('confidence_score', sa.Float, default=1.0, nullable=False),
        sa.Column('data_completeness', sa.Float, default=0.0, nullable=False),

        # Refresh tracking
        sa.Column('last_refreshed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('refresh_interval_hours', sa.Integer, default=24, nullable=False),
        sa.Column('auto_refresh_enabled', sa.Boolean, default=True, nullable=False),

        # Raw data for debugging/future use
        sa.Column('raw_data', postgresql.JSONB, nullable=True),

        # Unique constraint on source + id combination
        sa.UniqueConstraint('source_indexer', 'source_id', name='uq_source_indexer_id'),
    )
    
    # Create universal_manga_mappings table
    op.create_table(
        'universal_manga_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),

        sa.Column('manga_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('manga.id'), nullable=False),
        sa.Column('universal_entry_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('universal_manga_entries.id'), nullable=False),

        # Mapping confidence and source
        sa.Column('confidence_score', sa.Float, nullable=True),
        sa.Column('mapping_source', sa.String(50), nullable=False),
        sa.Column('verified_by_user', sa.Boolean, default=False, nullable=False),

        # Override settings
        sa.Column('use_universal_metadata', sa.Boolean, default=True, nullable=False),
        sa.Column('use_universal_cover', sa.Boolean, default=True, nullable=False),

        # Preferred indexer for this mapping
        sa.Column('preferred_indexer', sa.String(50), nullable=True),
    )

    # Create cross_indexer_references table
    op.create_table(
        'cross_indexer_references',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),

        # Primary universal entry (usually from highest tier indexer)
        sa.Column('universal_entry_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('universal_manga_entries.id'), nullable=False),

        # Reference to another indexer's entry for the same manga
        sa.Column('reference_indexer', sa.String(50), nullable=False),
        sa.Column('reference_id', sa.String(100), nullable=False),
        sa.Column('reference_url', sa.String(500), nullable=True),

        # Confidence in this cross-reference
        sa.Column('confidence_score', sa.Float, nullable=False, default=0.0),
        sa.Column('match_method', sa.String(50), nullable=False),

        # Verification status
        sa.Column('verified_by_user', sa.Boolean, default=False, nullable=False),
        sa.Column('verification_date', sa.DateTime(timezone=True), nullable=True),

        # Additional metadata from this reference
        sa.Column('additional_metadata', postgresql.JSONB, nullable=True),

        # Unique constraint to prevent duplicate references
        sa.UniqueConstraint('universal_entry_id', 'reference_indexer', 'reference_id', name='uq_cross_reference'),
    )
    
    # Create download_clients table
    op.create_table(
        'download_clients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('client_type', sa.String(20), nullable=False),  # "torrent", "nzb"
        sa.Column('implementation', sa.String(50), nullable=False),  # "qbittorrent", "deluge", "sabnzb", etc.
        
        # Connection settings
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer, nullable=False),
        sa.Column('use_ssl', sa.Boolean, default=False, nullable=False),
        sa.Column('username', sa.String(100), nullable=True),
        sa.Column('password', sa.String(255), nullable=True),  # Encrypted
        sa.Column('api_key', sa.String(255), nullable=True),
        
        # Client-specific settings
        sa.Column('settings', postgresql.JSONB, nullable=True),
        
        # Status and priority
        sa.Column('is_enabled', sa.Boolean, default=True, nullable=False),
        sa.Column('priority', sa.Integer, default=1, nullable=False),
        
        # Categories and paths
        sa.Column('default_category', sa.String(100), nullable=True),
        sa.Column('download_path', sa.String(500), nullable=True),
        
        # Health tracking
        sa.Column('last_test', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_healthy', sa.Boolean, default=True, nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
    )
    
    # Create indexers table
    op.create_table(
        'indexers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('indexer_type', sa.String(20), nullable=False),  # "torrent", "nzb"
        sa.Column('implementation', sa.String(50), nullable=False),  # "nyaa", "1337x", "nzbgeek", etc.
        
        # Connection settings
        sa.Column('base_url', sa.String(500), nullable=False),
        sa.Column('api_key', sa.String(255), nullable=True),
        sa.Column('username', sa.String(100), nullable=True),
        sa.Column('password', sa.String(255), nullable=True),  # Encrypted
        
        # Indexer capabilities
        sa.Column('supports_search', sa.Boolean, default=True, nullable=False),
        sa.Column('supports_rss', sa.Boolean, default=False, nullable=False),
        
        # Settings
        sa.Column('settings', postgresql.JSONB, nullable=True),
        
        # Status and priority
        sa.Column('is_enabled', sa.Boolean, default=True, nullable=False),
        sa.Column('priority', sa.Integer, default=1, nullable=False),
        
        # Health tracking
        sa.Column('last_test', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_healthy', sa.Boolean, default=True, nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
        
        # Rate limiting
        sa.Column('requests_per_day', sa.Integer, nullable=True),
        sa.Column('requests_today', sa.Integer, default=0, nullable=False),
        sa.Column('last_request_reset', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Create downloads table
    op.create_table(
        'downloads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        
        # What's being downloaded
        sa.Column('manga_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('manga.id'), nullable=True),
        sa.Column('chapter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chapter.id'), nullable=True),
        
        # Download source and method
        sa.Column('download_type', sa.String(20), nullable=False),  # "provider", "torrent", "nzb"
        sa.Column('source_name', sa.String(100), nullable=True),  # Provider/indexer name
        
        # Download client (for torrent/NZB)
        sa.Column('client_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('download_clients.id'), nullable=True),
        sa.Column('external_download_id', sa.String(255), nullable=True),  # ID in download client
        
        # Download details
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('download_url', sa.String(1000), nullable=True),
        sa.Column('magnet_link', sa.Text, nullable=True),
        sa.Column('torrent_hash', sa.String(40), nullable=True),
        
        # Status tracking
        sa.Column('status', sa.String(20), nullable=False, default='queued'),
        sa.Column('progress', sa.Float, default=0.0, nullable=False),
        
        # File information
        sa.Column('total_size', sa.Integer, nullable=True),  # Bytes
        sa.Column('downloaded_size', sa.Integer, default=0, nullable=False),  # Bytes
        sa.Column('download_speed', sa.Integer, nullable=True),  # Bytes per second
        sa.Column('eta', sa.Integer, nullable=True),  # Seconds
        
        # Paths
        sa.Column('download_path', sa.String(500), nullable=True),
        sa.Column('final_path', sa.String(500), nullable=True),
        
        # Timestamps
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        
        # Error handling
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, default=0, nullable=False),
        sa.Column('max_retries', sa.Integer, default=3, nullable=False),
    )
    
    # Create indexes
    op.create_index('idx_universal_entries_source_indexer', 'universal_manga_entries', ['source_indexer'])
    op.create_index('idx_universal_entries_source_id', 'universal_manga_entries', ['source_id'])
    op.create_index('idx_universal_entries_title', 'universal_manga_entries', ['title'])
    op.create_index('idx_universal_entries_confidence', 'universal_manga_entries', ['confidence_score'])
    op.create_index('idx_universal_mappings_manga_id', 'universal_manga_mappings', ['manga_id'])
    op.create_index('idx_universal_mappings_entry_id', 'universal_manga_mappings', ['universal_entry_id'])
    op.create_index('idx_cross_references_entry_id', 'cross_indexer_references', ['universal_entry_id'])
    op.create_index('idx_cross_references_indexer', 'cross_indexer_references', ['reference_indexer'])
    op.create_index('idx_download_clients_type_enabled', 'download_clients', ['client_type', 'is_enabled'])
    op.create_index('idx_indexers_type_enabled', 'indexers', ['indexer_type', 'is_enabled'])
    op.create_index('idx_downloads_status', 'downloads', ['status'])
    op.create_index('idx_downloads_manga_id', 'downloads', ['manga_id'])
    op.create_index('idx_downloads_chapter_id', 'downloads', ['chapter_id'])


def downgrade() -> None:
    """Remove MangaUpdates integration and download client support."""
    
    # Drop indexes
    op.drop_index('idx_downloads_chapter_id')
    op.drop_index('idx_downloads_manga_id')
    op.drop_index('idx_downloads_status')
    op.drop_index('idx_indexers_type_enabled')
    op.drop_index('idx_download_clients_type_enabled')
    op.drop_index('idx_cross_references_indexer')
    op.drop_index('idx_cross_references_entry_id')
    op.drop_index('idx_universal_mappings_entry_id')
    op.drop_index('idx_universal_mappings_manga_id')
    op.drop_index('idx_universal_entries_confidence')
    op.drop_index('idx_universal_entries_title')
    op.drop_index('idx_universal_entries_source_id')
    op.drop_index('idx_universal_entries_source_indexer')

    # Drop tables (in reverse order due to foreign keys)
    op.drop_table('downloads')
    op.drop_table('indexers')
    op.drop_table('download_clients')
    op.drop_table('cross_indexer_references')
    op.drop_table('universal_manga_mappings')
    op.drop_table('universal_manga_entries')
