"""Add unique constraint to manga_user_library table

Revision ID: 013
Revises: 012
Create Date: 2025-08-11 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add unique constraint to manga_user_library table."""
    # Add unique constraint on user_id and manga_id combination
    op.create_unique_constraint(
        'uq_manga_user_library_user_manga',
        'manga_user_library',
        ['user_id', 'manga_id']
    )


def downgrade() -> None:
    """Remove unique constraint from manga_user_library table."""
    op.drop_constraint(
        'uq_manga_user_library_user_manga',
        'manga_user_library',
        type_='unique'
    )
