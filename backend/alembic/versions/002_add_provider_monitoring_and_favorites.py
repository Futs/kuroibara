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
    # Check if users table exists and add column only if it doesn't exist
    from alembic import context
    conn = context.get_bind()
    inspector = sa.inspect(conn)
    
    if 'users' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('users')]
        if 'provider_check_interval' not in existing_columns:
            op.add_column('users', sa.Column('provider_check_interval', sa.Integer(), nullable=False, server_default='60'))
    
    # Create provider_status table only if it doesn't exist
    table_created = False
    if 'provider_status' not in inspector.get_table_names():
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
        table_created = True
    
    # Create indexes only if table was just created or indexes don't exist
    if table_created or 'provider_status' in inspector.get_table_names():
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('provider_status')]
        
        if 'ix_provider_status_provider_id' not in existing_indexes:
            op.create_index(op.f('ix_provider_status_provider_id'), 'provider_status', ['provider_id'], unique=True)
        
        if 'ix_provider_status_status' not in existing_indexes:
            op.create_index(op.f('ix_provider_status_status'), 'provider_status', ['status'])
        
        if 'ix_provider_status_is_enabled' not in existing_indexes:
            op.create_index(op.f('ix_provider_status_is_enabled'), 'provider_status', ['is_enabled'])
        
        if 'ix_provider_status_last_check' not in existing_indexes:
            op.create_index(op.f('ix_provider_status_last_check'), 'provider_status', ['last_check'])


def downgrade() -> None:
    # Check if table exists before attempting to drop indexes and table
    from alembic import context
    conn = context.get_bind()
    inspector = sa.inspect(conn)
    
    if 'provider_status' in inspector.get_table_names():
        # Check which indexes exist before dropping them
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('provider_status')]
        
        if 'ix_provider_status_last_check' in existing_indexes:
            op.drop_index(op.f('ix_provider_status_last_check'), table_name='provider_status')
        
        if 'ix_provider_status_is_enabled' in existing_indexes:
            op.drop_index(op.f('ix_provider_status_is_enabled'), table_name='provider_status')
        
        if 'ix_provider_status_status' in existing_indexes:
            op.drop_index(op.f('ix_provider_status_status'), table_name='provider_status')
        
        if 'ix_provider_status_provider_id' in existing_indexes:
            op.drop_index(op.f('ix_provider_status_provider_id'), table_name='provider_status')
        
        # Drop the table
        op.drop_table('provider_status')
    
    # Remove provider_check_interval from users table if it exists
    if 'users' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('users')]
        if 'provider_check_interval' in existing_columns:
            op.drop_column('users', 'provider_check_interval')
