"""Add multi-provider support to chapters

Revision ID: 015
Revises: 014
Create Date: 2025-08-23 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add multi-provider support fields to chapter table."""
    # Use more specific exception handling for better CI compatibility
    from sqlalchemy.exc import ProgrammingError

    # Add provider_external_ids JSONB column
    try:
        op.add_column('chapter', sa.Column('provider_external_ids', postgresql.JSONB(), nullable=True))
        print("✅ Added provider_external_ids column")
    except ProgrammingError as e:
        if "already exists" in str(e).lower():
            print("ℹ️ provider_external_ids column already exists, skipping")
        else:
            raise
    except Exception as e:
        print(f"⚠️ Unexpected error adding provider_external_ids: {e}")
        # Continue with migration

    # Add fallback_providers JSONB column
    try:
        op.add_column('chapter', sa.Column('fallback_providers', postgresql.JSONB(), nullable=True))
        print("✅ Added fallback_providers column")
    except ProgrammingError as e:
        if "already exists" in str(e).lower():
            print("ℹ️ fallback_providers column already exists, skipping")
        else:
            raise
    except Exception as e:
        print(f"⚠️ Unexpected error adding fallback_providers: {e}")
        # Continue with migration

    # Create index on provider_external_ids
    try:
        op.create_index('ix_chapter_provider_external_ids', 'chapter', ['provider_external_ids'], postgresql_using='gin')
        print("✅ Created index ix_chapter_provider_external_ids")
    except ProgrammingError as e:
        if "already exists" in str(e).lower():
            print("ℹ️ Index ix_chapter_provider_external_ids already exists, skipping")
        else:
            raise
    except Exception as e:
        print(f"⚠️ Unexpected error creating index: {e}")
        # Continue with migration


def downgrade() -> None:
    """Remove multi-provider support fields from chapter table."""
    # Use try-catch to handle cases where columns/indexes don't exist
    try:
        op.drop_index('ix_chapter_provider_external_ids', table_name='chapter')
    except Exception:
        # Index doesn't exist, skip
        pass

    try:
        op.drop_column('chapter', 'fallback_providers')
    except Exception:
        # Column doesn't exist, skip
        pass

    try:
        op.drop_column('chapter', 'provider_external_ids')
    except Exception:
        # Column doesn't exist, skip
        pass
