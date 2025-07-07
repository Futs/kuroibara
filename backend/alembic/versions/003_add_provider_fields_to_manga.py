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
    # Add provider fields to manga table
    op.add_column('manga', sa.Column('provider', sa.String(length=50), nullable=True))
    op.add_column('manga', sa.Column('external_id', sa.String(length=255), nullable=True))
    op.add_column('manga', sa.Column('external_url', sa.String(length=500), nullable=True))
    
    # Add indexes for better performance
    op.create_index(op.f('ix_manga_provider'), 'manga', ['provider'], unique=False)
    op.create_index(op.f('ix_manga_external_id'), 'manga', ['external_id'], unique=False)


def downgrade() -> None:
    # Remove indexes
    op.drop_index(op.f('ix_manga_external_id'), table_name='manga')
    op.drop_index(op.f('ix_manga_provider'), table_name='manga')
    
    # Remove columns
    op.drop_column('manga', 'external_url')
    op.drop_column('manga', 'external_id')
    op.drop_column('manga', 'provider')
