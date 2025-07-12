"""Add organization and metadata tracking models

Revision ID: 007
Revises: 006
Create Date: 2025-07-10 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Create manga_metadata table
    op.create_table('manga_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('manga_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('custom_cover_url', sa.String(length=500), nullable=True),
        sa.Column('custom_description', sa.Text(), nullable=True),
        sa.Column('is_organized', sa.Boolean(), nullable=False),
        sa.Column('organization_format', sa.String(length=500), nullable=True),
        sa.Column('last_organized_at', sa.DateTime(), nullable=True),
        sa.Column('last_read_at', sa.DateTime(), nullable=True),
        sa.Column('reading_status', sa.String(length=20), nullable=False),
        sa.Column('custom_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['manga_id'], ['manga.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('manga_id')
    )
    op.create_index(op.f('ix_manga_metadata_id'), 'manga_metadata', ['id'], unique=False)

    # Create chapter_metadata table
    op.create_table('chapter_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('chapter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('custom_cover_url', sa.String(length=500), nullable=True),
        sa.Column('is_organized', sa.Boolean(), nullable=False),
        sa.Column('organized_path', sa.String(length=500), nullable=True),
        sa.Column('original_path', sa.String(length=500), nullable=True),
        sa.Column('cbz_path', sa.String(length=500), nullable=True),
        sa.Column('current_page', sa.Integer(), nullable=False),
        sa.Column('total_pages', sa.Integer(), nullable=True),
        sa.Column('reading_progress', sa.Integer(), nullable=False),
        sa.Column('last_read_at', sa.DateTime(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=False),
        sa.Column('custom_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapter.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chapter_id')
    )
    op.create_index(op.f('ix_chapter_metadata_id'), 'chapter_metadata', ['id'], unique=False)

    # Create organization_history table
    op.create_table('organization_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('manga_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('chapter_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('operation_type', sa.String(length=50), nullable=False),
        sa.Column('operation_status', sa.String(length=20), nullable=False),
        sa.Column('source_path', sa.String(length=500), nullable=True),
        sa.Column('destination_path', sa.String(length=500), nullable=True),
        sa.Column('backup_path', sa.String(length=500), nullable=True),
        sa.Column('naming_format_used', sa.String(length=500), nullable=True),
        sa.Column('files_processed', sa.Integer(), nullable=False),
        sa.Column('errors_encountered', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('warnings_encountered', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('operation_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapter.id'], ),
        sa.ForeignKeyConstraint(['manga_id'], ['manga.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_history_id'), 'organization_history', ['id'], unique=False)

    # Create organization_jobs table
    op.create_table('organization_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('job_status', sa.String(length=20), nullable=False),
        sa.Column('total_items', sa.Integer(), nullable=False),
        sa.Column('processed_items', sa.Integer(), nullable=False),
        sa.Column('successful_items', sa.Integer(), nullable=False),
        sa.Column('failed_items', sa.Integer(), nullable=False),
        sa.Column('job_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('naming_format_manga', sa.String(length=500), nullable=True),
        sa.Column('naming_format_chapter', sa.String(length=500), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('estimated_completion', sa.DateTime(), nullable=True),
        sa.Column('result_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_log', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_jobs_id'), 'organization_jobs', ['id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_organization_jobs_id'), table_name='organization_jobs')
    op.drop_table('organization_jobs')
    
    op.drop_index(op.f('ix_organization_history_id'), table_name='organization_history')
    op.drop_table('organization_history')
    
    op.drop_index(op.f('ix_chapter_metadata_id'), table_name='chapter_metadata')
    op.drop_table('chapter_metadata')
    
    op.drop_index(op.f('ix_manga_metadata_id'), table_name='manga_metadata')
    op.drop_table('manga_metadata')
