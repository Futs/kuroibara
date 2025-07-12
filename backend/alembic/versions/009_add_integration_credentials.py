"""Add client credentials to external integrations

Revision ID: 009
Revises: 008
Create Date: 2024-12-07 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add client_id and client_secret columns to external_integrations table."""
    
    # Add client_id column
    op.add_column('external_integrations', 
                  sa.Column('client_id', sa.Text(), nullable=True))
    
    # Add client_secret column
    op.add_column('external_integrations', 
                  sa.Column('client_secret', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove client credentials columns."""
    
    # Remove client_secret column
    op.drop_column('external_integrations', 'client_secret')
    
    # Remove client_id column
    op.drop_column('external_integrations', 'client_id')
