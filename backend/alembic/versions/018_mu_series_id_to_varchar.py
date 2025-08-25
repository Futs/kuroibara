"""Change mu_series_id to VARCHAR

Revision ID: 018_mu_series_id_to_varchar
Revises: 017_bigint_mu_series
Create Date: 2025-08-25 18:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '018_mu_series_id_to_varchar'
down_revision = '017_bigint_mu_series'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Change mu_series_id from BIGINT to VARCHAR(100)
    op.alter_column('mangaupdates_entries', 'mu_series_id',
                   existing_type=sa.BigInteger(),
                   type_=sa.String(100),
                   existing_nullable=False)


def downgrade() -> None:
    # Change mu_series_id back from VARCHAR(100) to BIGINT
    op.alter_column('mangaupdates_entries', 'mu_series_id',
                   existing_type=sa.String(100),
                   type_=sa.BigInteger(),
                   existing_nullable=False)
