"""Add provider monitoring and favorites enhancements

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add provider_check_interval to users table
    op.add_column('users', sa.Column('provider_check_interval', sa.Integer(), nullable=False, server_default='60'))
    
    # Create provider_status table
    op.create_table('provider_status',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('provider_id', sa.String(length=100), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('provider_url', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='unknown'),
        sa.Column('last_check', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('response_time', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_checks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_checks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('uptime_percentage', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('check_interval', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('max_consecutive_failures', sa.Integer(), nullable=False, server_default='3'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_provider_status_provider_id'), 'provider_status', ['provider_id'], unique=True)
    op.create_index(op.f('ix_provider_status_status'), 'provider_status', ['status'])
    op.create_index(op.f('ix_provider_status_is_enabled'), 'provider_status', ['is_enabled'])
    op.create_index(op.f('ix_provider_status_last_check'), 'provider_status', ['last_check'])


def downgrade() -> None:
    # Drop provider_status table and indexes
    op.drop_index(op.f('ix_provider_status_last_check'), table_name='provider_status')
    op.drop_index(op.f('ix_provider_status_is_enabled'), table_name='provider_status')
    op.drop_index(op.f('ix_provider_status_status'), table_name='provider_status')
    op.drop_index(op.f('ix_provider_status_provider_id'), table_name='provider_status')
    op.drop_table('provider_status')
    
    # Remove provider_check_interval from users table
    op.drop_column('users', 'provider_check_interval')
