"""Add provider fields to manga table

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if manga table exists and add columns only if they don't exist
    from alembic import context
    conn = context.get_bind()
    inspector = sa.inspect(conn)
    
    if 'manga' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('manga')]
        
        # Add provider fields to manga table only if they don't exist
        if 'provider' not in existing_columns:
            op.add_column('manga', sa.Column('provider', sa.String(length=50), nullable=True))
            
        if 'external_id' not in existing_columns:
            op.add_column('manga', sa.Column('external_id', sa.String(length=255), nullable=True))
            
        if 'external_url' not in existing_columns:
            op.add_column('manga', sa.Column('external_url', sa.String(length=500), nullable=True))
        
        # Add indexes for better performance only if they don't exist
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('manga')]
        
        if 'ix_manga_provider' not in existing_indexes:
            op.create_index(op.f('ix_manga_provider'), 'manga', ['provider'], unique=False)
            
        if 'ix_manga_external_id' not in existing_indexes:
            op.create_index(op.f('ix_manga_external_id'), 'manga', ['external_id'], unique=False)


def downgrade() -> None:
    # Check if table exists before attempting to drop indexes and columns
    from alembic import context
    conn = context.get_bind()
    inspector = sa.inspect(conn)
    
    if 'manga' in inspector.get_table_names():
        # Check which indexes exist before dropping them
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('manga')]
        
        if 'ix_manga_external_id' in existing_indexes:
            op.drop_index(op.f('ix_manga_external_id'), table_name='manga')
            
        if 'ix_manga_provider' in existing_indexes:
            op.drop_index(op.f('ix_manga_provider'), table_name='manga')
        
        # Check which columns exist before dropping them
        existing_columns = [col['name'] for col in inspector.get_columns('manga')]
        
        if 'external_url' in existing_columns:
            op.drop_column('manga', 'external_url')
            
        if 'external_id' in existing_columns:
            op.drop_column('manga', 'external_id')
            
        if 'provider' in existing_columns:
            op.drop_column('manga', 'provider')
