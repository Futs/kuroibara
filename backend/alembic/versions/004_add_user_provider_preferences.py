"""Add user provider preferences

Revision ID: 004
Revises: 003
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_provider_preferences table
    op.create_table('user_provider_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', sa.String(length=100), nullable=False),
        sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('priority_order', sa.Integer(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'provider_id', name='uq_user_provider')
    )
    
    # Create indexes for better query performance
    op.create_index(op.f('ix_user_provider_preferences_user_id'), 'user_provider_preferences', ['user_id'])
    op.create_index(op.f('ix_user_provider_preferences_provider_id'), 'user_provider_preferences', ['provider_id'])
    op.create_index(op.f('ix_user_provider_preferences_is_favorite'), 'user_provider_preferences', ['is_favorite'])
    op.create_index(op.f('ix_user_provider_preferences_priority_order'), 'user_provider_preferences', ['priority_order'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_user_provider_preferences_priority_order'), table_name='user_provider_preferences')
    op.drop_index(op.f('ix_user_provider_preferences_is_favorite'), table_name='user_provider_preferences')
    op.drop_index(op.f('ix_user_provider_preferences_provider_id'), table_name='user_provider_preferences')
    op.drop_index(op.f('ix_user_provider_preferences_user_id'), table_name='user_provider_preferences')
    
    # Drop table
    op.drop_table('user_provider_preferences')
