"""Add external account links to user profile

Revision ID: 001
Revises: 
Create Date: 2024-05-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add external account link columns to users table."""
    # Check if table exists and add columns only if they don't exist
    from alembic import context
    conn = context.get_bind()
    
    # Check if users table exists
    inspector = sa.inspect(conn)
    if 'users' not in inspector.get_table_names():
        print("Warning: users table does not exist, skipping migration 001")
        return
    
    # Check if columns already exist
    existing_columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'anilist_username' not in existing_columns:
        op.add_column('users', sa.Column('anilist_username', sa.String(100), nullable=True))
    
    if 'myanimelist_username' not in existing_columns:
        op.add_column('users', sa.Column('myanimelist_username', sa.String(100), nullable=True))


def downgrade() -> None:
    """Remove external account link columns from users table."""
    # Check if table exists and remove columns only if they exist
    from alembic import context
    conn = context.get_bind()
    
    # Check if users table exists
    inspector = sa.inspect(conn)
    if 'users' not in inspector.get_table_names():
        print("Warning: users table does not exist, skipping migration 001 downgrade")
        return
    
    # Check if columns exist before dropping
    existing_columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'myanimelist_username' in existing_columns:
        op.drop_column('users', 'myanimelist_username')
    
    if 'anilist_username' in existing_columns:
        op.drop_column('users', 'anilist_username')
