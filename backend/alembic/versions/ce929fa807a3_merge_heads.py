"""merge_heads

Revision ID: ce929fa807a3
Revises: 014, add_multi_provider_support
Create Date: 2025-08-22 19:03:27.246436

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce929fa807a3'
down_revision = ('014', 'add_multi_provider_support')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
