"""Add publish_at and readable_at to chapters

Revision ID: 010
Revises: 009
Create Date: 2025-07-18 20:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add publish_at and readable_at columns to chapter table
    op.add_column('chapter', sa.Column('publish_at', sa.DateTime(), nullable=True))
    op.add_column('chapter', sa.Column('readable_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove the columns
    op.drop_column('chapter', 'readable_at')
    op.drop_column('chapter', 'publish_at')
