"""Add external account links to user profile

Revision ID: 001
Revises: 
Create Date: 2024-05-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add external account link columns to users table."""
    # Add new columns to users table
    op.add_column('users', sa.Column('anilist_username', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('myanimelist_username', sa.String(100), nullable=True))


def downgrade() -> None:
    """Remove external account link columns from users table."""
    # Remove columns from users table
    op.drop_column('users', 'myanimelist_username')
    op.drop_column('users', 'anilist_username')
