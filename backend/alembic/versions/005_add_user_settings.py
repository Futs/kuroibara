"""Add user settings fields

Revision ID: 005
Revises: 004
Create Date: 2025-07-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Add user settings columns to users table
    op.add_column('users', sa.Column('theme', sa.String(20), nullable=False, server_default='light'))
    op.add_column('users', sa.Column('nsfw_blur', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('download_quality', sa.String(20), nullable=False, server_default='high'))
    op.add_column('users', sa.Column('download_path', sa.String(500), nullable=False, server_default='/app/storage'))


def downgrade():
    # Remove user settings columns from users table
    op.drop_column('users', 'download_path')
    op.drop_column('users', 'download_quality')
    op.drop_column('users', 'nsfw_blur')
    op.drop_column('users', 'theme')
