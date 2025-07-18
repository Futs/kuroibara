"""Add storage settings to user table

Revision ID: 011
Revises: 010
Create Date: 2025-07-18 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add storage_type and max_upload_size columns to users table
    op.add_column('users', sa.Column('storage_type', sa.String(20), nullable=False, server_default='local'))
    op.add_column('users', sa.Column('max_upload_size', sa.String(10), nullable=False, server_default='100MB'))


def downgrade() -> None:
    # Remove the columns
    op.drop_column('users', 'max_upload_size')
    op.drop_column('users', 'storage_type')
