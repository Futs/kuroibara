"""Change mu_series_id to BigInteger

Revision ID: 017_change_mu_series_id_to_biginteger
Revises: e1684e1a82ec
Create Date: 2025-08-25 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '017_bigint_mu_series'
down_revision = 'e1684e1a82ec'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Change mu_series_id from INTEGER to BIGINT
    op.alter_column('mangaupdates_entries', 'mu_series_id',
                   existing_type=sa.INTEGER(),
                   type_=sa.BigInteger(),
                   existing_nullable=False)


def downgrade() -> None:
    # Change mu_series_id back from BIGINT to INTEGER
    op.alter_column('mangaupdates_entries', 'mu_series_id',
                   existing_type=sa.BigInteger(),
                   type_=sa.INTEGER(),
                   existing_nullable=False)
