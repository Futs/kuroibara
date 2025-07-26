"""Create base tables

Revision ID: 000
Revises:
Create Date: 2025-07-10 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '000'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all base tables."""

    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('two_fa_secret', sa.String(length=32), nullable=True),
        sa.Column('two_fa_enabled', sa.Boolean(), nullable=False),
        sa.Column('avatar', sa.String(length=255), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('theme', sa.String(length=20), nullable=False),
        sa.Column('nsfw_blur', sa.Boolean(), nullable=False),
        sa.Column('download_quality', sa.String(length=20), nullable=False),
        sa.Column('download_path', sa.String(length=255), nullable=False),
        sa.Column('naming_format_manga', sa.String(length=500), nullable=False),
        sa.Column('naming_format_chapter', sa.String(length=500), nullable=False),
        sa.Column('preferred_structure_pattern', sa.String(length=50), nullable=False),
        sa.Column('auto_organize_imports', sa.Boolean(), nullable=False),
        sa.Column('create_cbz_files', sa.Boolean(), nullable=False),
        sa.Column('preserve_original_files', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create manga table
    op.create_table('manga',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('alternative_titles', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cover_image', sa.String(length=255), nullable=True),
        sa.Column('type', sa.Enum('MANGA', 'MANHUA', 'MANHWA', 'COMIC', 'UNKNOWN', name='mangatype'), nullable=False),
        sa.Column('status', sa.Enum('ONGOING', 'COMPLETED', 'HIATUS', 'CANCELLED', 'UNKNOWN', name='mangastatus'), nullable=False),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('is_nsfw', sa.Boolean(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('external_url', sa.String(length=500), nullable=True),
        sa.Column('external_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_manga_external_id'), 'manga', ['external_id'], unique=False)
    op.create_index(op.f('ix_manga_id'), 'manga', ['id'], unique=False)
    op.create_index(op.f('ix_manga_provider'), 'manga', ['provider'], unique=False)
    op.create_index(op.f('ix_manga_title'), 'manga', ['title'], unique=False)

    # Create genre table
    op.create_table('genre',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_genre_id'), 'genre', ['id'], unique=False)
    op.create_index(op.f('ix_genre_name'), 'genre', ['name'], unique=True)

    # Create author table
    op.create_table('author',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('alternative_names', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('biography', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_author_id'), 'author', ['id'], unique=False)
    op.create_index(op.f('ix_author_name'), 'author', ['name'], unique=True)

    # Create association tables
    op.create_table('manga_genre',
        sa.Column('manga_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('genre_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['genre_id'], ['genre.id'], ),
        sa.ForeignKeyConstraint(['manga_id'], ['manga.id'], ),
        sa.PrimaryKeyConstraint('manga_id', 'genre_id')
    )

    op.create_table('manga_author',
        sa.Column('manga_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['author.id'], ),
        sa.ForeignKeyConstraint(['manga_id'], ['manga.id'], ),
        sa.PrimaryKeyConstraint('manga_id', 'author_id')
    )

    # Create chapter table
    op.create_table('chapter',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('manga_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('number', sa.String(length=20), nullable=False),
        sa.Column('volume', sa.String(length=20), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('pages_count', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.String(length=255), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('external_url', sa.String(length=500), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['manga_id'], ['manga.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chapter_external_id'), 'chapter', ['external_id'], unique=False)
    op.create_index(op.f('ix_chapter_id'), 'chapter', ['id'], unique=False)
    op.create_index(op.f('ix_chapter_manga_id'), 'chapter', ['manga_id'], unique=False)

    # Create page table
    op.create_table('page',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('chapter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=False),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapter.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_page_id'), 'page', ['id'], unique=False)

    # Create category table
    op.create_table('category',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_category_id'), 'category', ['id'], unique=False)
    op.create_index(op.f('ix_category_name'), 'category', ['name'], unique=False)

    # Create manga_user_library table
    op.create_table('manga_user_library',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('manga_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('custom_title', sa.String(length=255), nullable=True),
        sa.Column('custom_cover', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_favorite', sa.Boolean(), nullable=False),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('is_downloaded', sa.Boolean(), nullable=False),
        sa.Column('download_path', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['manga_id'], ['manga.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_manga_user_library_id'), 'manga_user_library', ['id'], unique=False)

    # Create manga_user_library_category association table
    op.create_table('manga_user_library_category',
        sa.Column('manga_user_library_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['category.id'], ),
        sa.ForeignKeyConstraint(['manga_user_library_id'], ['manga_user_library.id'], ),
        sa.PrimaryKeyConstraint('manga_user_library_id', 'category_id')
    )

    # Create reading_list table
    op.create_table('reading_list',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reading_list_id'), 'reading_list', ['id'], unique=False)

    # Create reading_list_manga association table
    op.create_table('reading_list_manga',
        sa.Column('reading_list_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('manga_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['manga_id'], ['manga.id'], ),
        sa.ForeignKeyConstraint(['reading_list_id'], ['reading_list.id'], ),
        sa.PrimaryKeyConstraint('reading_list_id', 'manga_id')
    )

    # Create reading_progress table
    op.create_table('reading_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('manga_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chapter_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('page', sa.Integer(), nullable=False),
        sa.Column('total_pages', sa.Integer(), nullable=True),
        sa.Column('progress_percentage', sa.Float(), nullable=False),
        sa.Column('status', sa.Enum('READING', 'COMPLETED', 'DROPPED', 'PLAN_TO_READ', 'ON_HOLD', name='readingstatus'), nullable=False),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapter.id'], ),
        sa.ForeignKeyConstraint(['manga_id'], ['manga.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reading_progress_id'), 'reading_progress', ['id'], unique=False)

    # Create bookmark table
    op.create_table('bookmark',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('manga_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chapter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('page', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapter.id'], ),
        sa.ForeignKeyConstraint(['manga_id'], ['manga.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bookmark_id'), 'bookmark', ['id'], unique=False)

    # Create provider_status table
    op.create_table('provider_status',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('provider_id', sa.String(length=100), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('provider_url', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('last_check', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('response_time', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False),
        sa.Column('total_checks', sa.Integer(), nullable=False),
        sa.Column('successful_checks', sa.Integer(), nullable=False),
        sa.Column('uptime_percentage', sa.Integer(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('check_interval', sa.Integer(), nullable=False),
        sa.Column('max_consecutive_failures', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_provider_status_id'), 'provider_status', ['id'], unique=False)
    op.create_index(op.f('ix_provider_status_provider_id'), 'provider_status', ['provider_id'], unique=True)


def downgrade() -> None:
    """Drop all base tables."""
    # Drop tables in reverse order of creation
    op.drop_index(op.f('ix_provider_status_provider_id'), table_name='provider_status')
    op.drop_index(op.f('ix_provider_status_id'), table_name='provider_status')
    op.drop_table('provider_status')
    op.drop_index(op.f('ix_bookmark_id'), table_name='bookmark')
    op.drop_table('bookmark')
    op.drop_index(op.f('ix_reading_progress_id'), table_name='reading_progress')
    op.drop_table('reading_progress')
    op.drop_table('reading_list_manga')
    op.drop_index(op.f('ix_reading_list_id'), table_name='reading_list')
    op.drop_table('reading_list')
    op.drop_table('manga_user_library_category')
    op.drop_index(op.f('ix_manga_user_library_id'), table_name='manga_user_library')
    op.drop_table('manga_user_library')
    op.drop_index(op.f('ix_category_name'), table_name='category')
    op.drop_index(op.f('ix_category_id'), table_name='category')
    op.drop_table('category')
    op.drop_index(op.f('ix_page_id'), table_name='page')
    op.drop_table('page')
    op.drop_index(op.f('ix_chapter_manga_id'), table_name='chapter')
    op.drop_index(op.f('ix_chapter_id'), table_name='chapter')
    op.drop_index(op.f('ix_chapter_external_id'), table_name='chapter')
    op.drop_table('chapter')
    op.drop_table('manga_author')
    op.drop_table('manga_genre')
    op.drop_index(op.f('ix_author_name'), table_name='author')
    op.drop_index(op.f('ix_author_id'), table_name='author')
    op.drop_table('author')
    op.drop_index(op.f('ix_genre_name'), table_name='genre')
    op.drop_index(op.f('ix_genre_id'), table_name='genre')
    op.drop_table('genre')
    op.drop_index(op.f('ix_manga_title'), table_name='manga')
    op.drop_index(op.f('ix_manga_provider'), table_name='manga')
    op.drop_index(op.f('ix_manga_id'), table_name='manga')
    op.drop_index(op.f('ix_manga_external_id'), table_name='manga')
    op.drop_table('manga')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
